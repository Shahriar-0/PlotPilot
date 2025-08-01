import os
import click
import requests
from rich.console import Console
from rich.table import Table
import plotille
from dotenv import load_dotenv

load_dotenv()

console = Console()

API_KEY = os.getenv("OMDB_API_KEY")
BASE_URL = "http://www.omdbapi.com/"


@click.group()
def cli():
    """PlotPilot: Explore movie and series data in your terminal."""
    pass


@cli.command()
@click.argument("title")
def search(title):
    """Search for a movie or series by title and display detailed information."""
    params = {"apikey": API_KEY, "t": title}
    response = requests.get(BASE_URL, params=params).json()
    if response["Response"] == "True":
        if response["Type"] == "movie":
            console.print(f"[bold green]{response['Title']} ({response['Year']})[/]")
            console.print(f"Director: {response['Director']}")
            console.print(f"IMDb ID: {response['imdbID']}")
            console.print()
            console.print("[bold]Ratings:[/]")
            for rating in response.get("Ratings", []):
                console.print(f"• [cyan]{rating['Source']}[/]: {rating['Value']}")
            console.print()
            console.print(f"[bold]Plot:[/] {response['Plot']}")
        elif response["Type"] == "series":
            console.print(f"[bold green]{response['Title']} ({response['Year']})[/]")
            console.print(f"Total Seasons: {response['totalSeasons']}")
            console.print(f"IMDb ID: {response['imdbID']}")
            console.print()
            console.print("[bold]Ratings:[/]")
            for rating in response.get("Ratings", []):
                console.print(f"• [cyan]{rating['Source']}[/]: {rating['Value']}")
            console.print()
            console.print(f"[bold]Plot:[/] {response['Plot']}")
        else:
            console.print(f"[bold yellow]Type: {response['Type']}[/]")
            console.print(
                f"Title: {response['Title']}, Year: {response['Year']}, IMDb ID: {response['imdbID']}"
            )
    else:
        console.print("[bold red]Title not found![/]")


@cli.command()
@click.argument("imdb_id")
def synopsis(imdb_id):
    """Fetch the full synopsis for a movie or series."""
    params = {"apikey": API_KEY, "i": imdb_id, "plot": "full"}
    response = requests.get(BASE_URL, params=params).json()
    if response["Response"] == "True":
        console.print(f"[bold cyan]{response['Title']}\nSynopsis[/]")
        console.print(response["Plot"])
    else:
        console.print("[bold red]Invalid IMDb ID![/]")


@cli.command()
@click.argument("imdb_id")
@click.option("--season", default=1, help="Season number")
def episodes(imdb_id, season):
    """List episode summaries and ratings for a series."""
    params = {"apikey": API_KEY, "i": imdb_id, "season": season}
    response = requests.get(BASE_URL, params=params).json()
    if response["Response"] == "True" and "Episodes" in response:
        table = Table(title=f"{response['Title']} - Season {season}")
        table.add_column("Episode", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Rating", style="green")
        table.add_column("Summary", style="white")
        for ep in response["Episodes"]:
            table.add_row(ep["Episode"], ep["Title"], ep["imdbRating"], ep["Plot"])
        console.print(table)
    else:
        console.print("[bold red]No episodes found![/]")


@cli.command()
@click.argument("imdb_id")
@click.option("--season", default=1, help="Season number")
def ratings(imdb_id, season):
    """Visualize episode rating distribution for a series."""
    params = {"apikey": API_KEY, "i": imdb_id, "season": season}
    response = requests.get(BASE_URL, params=params).json()
    if response["Response"] == "True" and "Episodes" in response:
        episodes = response["Episodes"]
        ratings_data = [
            (int(ep["Episode"]), float(ep["imdbRating"]))
            for ep in episodes
            if ep["imdbRating"] != "N/A"
        ]
        if not ratings_data:
            console.print("[bold red]No ratings found![/]")
            return
        console.print(
            f"[bold yellow]{response['Title']} - Season {season} Rating Distribution[/]"
        )
        boxes = []
        for ep_num, rating in ratings_data:
            if rating >= 9.0:
                color = "dark_green"
            elif rating >= 8.0:
                color = "green"
            elif rating >= 7.0:
                color = "cyan"
            elif rating >= 6.0:
                color = "yellow"
            elif rating >= 5.0:
                color = "magenta"
            else:
                color = "red"
            box = f"[bold {color}]Ep {ep_num}: {rating:.3f}[/]"
            boxes.append(box)
        for i in range(0, len(boxes)):
            console.print("  ".join(boxes[i : i + 1]))
    else:
        console.print("[bold red]No ratings found![/]")


if __name__ == "__main__":
    cli()
