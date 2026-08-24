import shutil
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from typing import List,Optional,Required
import typer
from rich.progress import Progress,BarColumn,TextColumn,TimeRemainingColumn
from uuid import uuid4
import interactive
from env_check import ensure_env_ready
from download import download_video
from zip_files import zip_downloaded_files
from errors.errors import DownloadFailure,FetchError
from models.data_models import url_info,task_completion

app=typer.Typer(add_completion=True)

RETRYABLE={FetchError.RATE_LIMITED,FetchError.UNKNOWN}

@app.command()
def main(
    urls:List[str]=typer.Argument(
        None,help="One or more media urls. Omit for guided interactive mode."
    ),
    format:Optional[str]=typer.Option(
        None,'--format','-f',
        help="mp4 or mp3. Applies to every URL if set; otherwise asked per URL.",
    ),
    resolution:Optional[str]=typer.Option(
        None,'--resolution','-r',
        help="Best/480P/720P/1080P (mp4 only)."
    ),
    bitrate:Optional[str]=typer.Option(
        None,'--bitrate','-b',
        help="128k/192k/256k/320k (mp3 only)."
    ),
    output:Optional[Path]=typer.Option(
        None, "--output", "-o", help="Save directory. Prompted for if not set."
    ),
        workers: Optional[int] = typer.Option(
        None, "--workers", "-w", help="Max parallel downloads. Defaults to min(len(urls), 8)."
    ),
    zip_output: Optional[bool] = typer.Option(
        None, "--zip/--no-zip", help="Zip a multi-URL batch. Defaults to on for >1 URL."
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y",
        help="Never prompt anything not explicitly flagged uses a sane default instead.",
    ),
    retries: int = typer.Option(
        0, "--retries", help="Retry count for rate-limited/transient failures. 0 = no retry."
    ),
    continue_on_error: bool = typer.Option(
        True, "--continue-on-error/--stop-on-error",
        help="Keep downloading remaining URLs if one fails.",
    ),
):
    "Download Videos/Audio form the terminal."

    ensure_env_ready()

    urls=list(urls) if urls else []

    if not urls:
        urls=interactive.collect_urls(_ask_count())

    resolved_output=_resolve_output(output,yes)

    is_batch=len(urls)>1
    batch_folder=None
    if is_batch:
        appdata=Path.home()/'vidownload'
        appdata.mkdir(exist_ok=True,parents=True)
        batch_folder=appdata/f'batch_{uuid4().hex[:8]}'
        batch_folder.mkdir(exist_ok=True,parents=True)

    dest_for_downloads:Path=batch_folder if is_batch else resolved_output

    tasks:List[url_info]=[_build_task(url,dest_for_downloads,format,resolution,bitrate,yes)
           for url in urls]

    resolved_workers=workers or min(len(tasks),8)
    should_zip=zip_output if zip_output is not None else is_batch

    results:list[task_completion]=_download_all(tasks,resolved_workers,retries,continue_on_error)

    if is_batch and should_zip and batch_folder and batch_folder.exists():
        typer.secho('\n 📦 Zipping Files...',fg=typer.colors.CYAN)
        zip_downloaded_files(resolved_output,batch_folder)
        typer.secho(f'\n ✅ Zip complete: {resolved_output}',fg=typer.colors.BRIGHT_GREEN,bold=True)

    if batch_folder and batch_folder.exists():
        shutil.rmtree(batch_folder,ignore_errors=True)

    _print_summary(results)
    if any(not r.success for r in results):
        raise typer.Exit(code=1)



def _ask_count() -> int:
    "Asks the user for the amount of files to be downloaded"
    while True:
        raw = typer.prompt("How many files do you want to download?")
        try:
            n = int(raw)
            if n > 0:
                return n
            typer.secho("Please enter a number greater than 0.",fg=typer.colors.BRIGHT_YELLOW,bold=True)
        except ValueError:
            typer.secho("Please enter a valid number.",fg=typer.colors.BRIGHT_RED,bold=True)

def _resolve_output(output: Optional[Path], yes: bool) -> Path:
    "Gets the output directory if not exists makes one"
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        return output
    if yes:
        default = Path("downloads")
        default.mkdir(parents=True, exist_ok=True)
        return default
    return interactive.ask_output_path()

def _build_task(task_url:str, output_path:Path, task_format:str, resolution:str, bitrate:str, yes:bool) -> dict:

    if task_format is None:
        task_format = "mp4" if yes else interactive.ask_format()

    task_res = None
    task_bitrate = None
    if task_format == "mp4":
        task_res = resolution
        if task_res is None:
            task_res = "best" if yes else interactive.ask_resolution()
    else:
        task_bitrate = bitrate
        if task_bitrate is None:
            task_bitrate = "192k" if yes else interactive.ask_bitrate()
 
    return url_info(
        url=task_url,
        file_type=task_format.lower(),
        selected_res=task_res.lower() if task_res is not None else task_res,
        audio_quality=task_bitrate.lower() if task_bitrate is not None else task_bitrate,
        output_path=output_path
    )

def _download_all(tasks:list[url_info],max_workers,retries,continue_on_error) -> list:
    results:list[task_completion]=[]
    stop_requested=False

    with Progress(
        TextColumn("[bold blue]{task.fields[label]}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        TimeRemainingColumn()) as progress:

        progress_ids={task.url:progress.add_task('download',label=_short(task.url),total=100)
            for task in tasks
        }

        def run_one(task:url_info):
            attempt=0
            task_id=progress_ids[task.url]

            def on_progress(pct):
                progress.update(task_id,completed=pct*100)

            while True:
                try:
                    download_video(
                        url=task.url,
                        selected_res=task.selected_res,
                        audio_quality=task.audio_quality,
                        file_type=task.file_type,
                        output_path=task.output_path,
                        progress_callback=on_progress,
                    )
                    return task_completion(
                        url=task.url,
                        success=True,
                        error_type=None,
                        message=None
                    )
                except DownloadFailure as e:
                    if e.error_type in RETRYABLE and attempt<retries:
                        attempt+=1
                        progress.update(task_id,completed=0)
                        continue

                    return task_completion(
                        url=task.url,
                        success=False,
                        error_type=e.error_type,
                        message=str(e)
                    )
                except Exception as e:
                    return task_completion(
                        url=task.url,
                        success=False,
                        error_type=FetchError.UNKNOWN,
                        message=str(e)
                    )
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures={executor.submit(run_one,task) for task in tasks}
            for future in as_completed(futures):
                results.append(future.result())
                if not results[-1].success and not continue_on_error:
                    stop_requested=True
                    for f in futures:
                        f.cancel()
                    break
    if stop_requested:
        typer.secho("\nStopped after a failure (--stop-on-error).",fg=typer.colors.BRIGHT_RED,bold=True)

    return results


def _short(url, length=45):
    return url if len(url) <= length else url[: length - 1] + "…"

def _print_summary(results:list[task_completion]):
    ok = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    typer.secho(f"\n{len(ok)} succeeded, {len(failed)} failed.",fg=typer.colors.BRIGHT_CYAN)
    for r in failed:
        typer.secho(f"  ✗ {r.url} — {r.message}",fg=typer.colors.BRIGHT_RED,bold=True)


if __name__=='__main__':
    app()