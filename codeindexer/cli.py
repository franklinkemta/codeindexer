"""Command-line interface for CodeIndexer."""

import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress

from .indexer import create_index

console = Console()

@click.command()
@click.option(
    "--index",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help="Directory to index",
)
@click.option(
    "--only",
    default="",
    help="Comma-separated list of file extensions to include (e.g., .py,.js,.md)",
)
@click.option(
    "--skip",
    default="",
    help="Comma-separated list of patterns to skip (e.g., node_modules/,venv/,*.log)",
)
@click.option(
    "--include",
    default="",
    help="Comma-separated list of patterns to explicitly include even if in .gitignore",
)
@click.option(
    "--format",
    "output_format",
    default="md",
    type=click.Choice(["md", "txt", "json"]),
    help="Output format (md, txt, json)",
)
@click.option(
    "--prompt",
    default="Acknowledge the project's description and files, do no provide additional explanation, wait for instructions",
    help="Custom prompt to add at the end of the index",
)
@click.option(
    "--skip-env/--no-skip-env",
    default=True,
    help="Skip .env files (default: True)",
)
@click.option(
    "--use-gitignore/--no-gitignore",
    default=True,
    help="Use .gitignore patterns (default: True)",
)
@click.option(
    "--split",
    type=int,
    is_flag=False,
    flag_value=1000,
    default=None,
    help="Split output into chunks with specified max lines per file (default: 1000)",
)
@click.argument("output_file", type=click.Path(resolve_path=True))
def main(
    index, only, skip, include, output_format, prompt, 
    skip_env, use_gitignore, split, output_file
):
    """Generate an index of a codebase for LLM context."""
    try:
        index_dir = Path(index)
        output_path = Path(output_file)

        # Process options
        only_extensions = [ext.strip() for ext in only.split(",")] if only else []
        skip_patterns = [pattern.strip() for pattern in skip.split(",")] if skip else []
        include_patterns = [pattern.strip() for pattern in include.split(",")] if include else []
        
        if skip_env and ".env" not in skip_patterns:
            skip_patterns.append("*.env")
        
        with Progress() as progress:
            # Create the main task
            main_task = progress.add_task("[green]Indexing codebase...", total=100)
            console.log("\n")
            
            # Define the progress callback
            def update_progress(status, current, total, message=None):
                if total > 0:
                    progress.update(main_task, completed=int(current / total * 100), description=f"[green]{status}...")
                if message:
                    console.log(message)
            
            create_index(
                index_dir=index_dir,
                output_path=output_path,
                only_extensions=only_extensions,
                skip_patterns=skip_patterns,
                include_patterns=include_patterns,
                output_format=output_format,
                prompt=prompt,
                use_gitignore=use_gitignore,
                split_max_lines=split,
                progress_callback=update_progress,
            )
        
        if split:
            split_dir = output_path.parent / output_path.stem
            console.print(f"✅ Prompt file parts: [bold green]{split_dir}/[/]")
        else:
            console.print(f"✅ Prompt file: [bold green]{output_path}[/]")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise click.Abort()

if __name__ == "__main__":
    main()
