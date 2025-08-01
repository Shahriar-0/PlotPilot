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
        t = response["Type"]

        title = response.get("Title", "N/A")
        year = response.get("Year", "N/A")
        genre = response.get("Genre", "N/A")
        runtime = response.get("Runtime", "N/A")
        language = response.get("Language", "N/A")
        country = response.get("Country", "N/A")
        awards = response.get("Awards", "N/A")
        poster = response.get("Poster", "N/A")
        plot = response.get("Plot", "N/A")
        imdb_id = response.get("imdbID", "N/A")
        imdb_rating = response.get("imdbRating", "N/A")
        imdb_votes = response.get("imdbVotes", "N/A")
        ratings = response.get("Ratings", [])
        actors = response.get("Actors", "N/A")
        writer = response.get("Writer", "N/A")
        director = response.get("Director", "N/A")
        box_office = response.get("BoxOffice", "N/A")
        metascore = response.get("Metascore", "N/A")

        if t == "movie":
            console.print(f"[bold green]{title} ({year})[/]")
            console.print(f"[bold]Genre:[/] {genre}")
            console.print(f"[bold]Runtime:[/] {runtime}")
            console.print(f"[bold]Language:[/] {language}")
            console.print(f"[bold]Country:[/] {country}")
            console.print(f"[bold]Director:[/] {director}")
            console.print(f"[bold]Writer:[/] {writer}")
            console.print(f"[bold]Actors:[/] {actors}")
            console.print(f"[bold]IMDb ID:[/] {imdb_id}")
            console.print(f"[bold]IMDb Rating:[/] {imdb_rating} ({imdb_votes} votes)")
            console.print(f"[bold]Metascore:[/] {metascore}")
            console.print(f"[bold]Box Office:[/] {box_office}")
            console.print(f"[bold]Awards:[/] {awards}")
            if poster and poster != "N/A":
                console.print(f"[bold]Poster:[/] {poster}")
            console.print()
            if ratings:
                console.print("[bold]Ratings:[/]")
                for rating in ratings:
                    console.print(f"• [cyan]{rating['Source']}[/]: {rating['Value']}")
                console.print()
            console.print(f"[bold]Plot:[/] {plot}")
        elif t == "series":
            total_seasons = response.get("totalSeasons", "N/A")
            console.print(f"[bold green]{title} ({year})[/]")
            console.print(f"[bold]Genre:[/] {genre}")
            console.print(f"[bold]Runtime:[/] {runtime}")
            console.print(f"[bold]Language:[/] {language}")
            console.print(f"[bold]Country:[/] {country}")
            console.print(f"[bold]Writer:[/] {writer}")
            console.print(f"[bold]Actors:[/] {actors}")
            console.print(f"[bold]IMDb ID:[/] {imdb_id}")
            console.print(f"[bold]IMDb Rating:[/] {imdb_rating} ({imdb_votes} votes)")
            console.print(f"[bold]Total Seasons:[/] {total_seasons}")
            console.print(f"[bold]Awards:[/] {awards}")
            if poster and poster != "N/A":
                console.print(f"[bold]Poster:[/] {poster}")
            console.print()
            if ratings:
                console.print("[bold]Ratings:[/]")
                for rating in ratings:
                    console.print(f"• [cyan]{rating['Source']}[/]: {rating['Value']}")
                console.print()
            console.print(f"[bold]Plot:[/] {plot}")
        else:
            console.print(f"[bold yellow]Type: {t}[/]")
            console.print(f"Title: {title}, Year: {year}, IMDb ID: {imdb_id}")
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
@click.option(
    "--season", default=None, type=int, help="Season number (if omitted, show all)"
)
def ratings(imdb_id, season):
    """Visualize episode rating distribution for a series. If no season is provided, show all seasons in columns."""

    def get_color(rating):
        if rating >= 9.0:
            return "dark_green"
        elif rating >= 8.0:
            return "green"
        elif rating >= 7.0:
            return "cyan"
        elif rating >= 6.0:
            return "yellow"
        elif rating >= 5.0:
            return "magenta"
        else:
            return "red"

    def format_box(text, color=None, width=15):
        if color:
            return f"[bold {color}]{text:<{width}}[/]"
        else:
            return f"[dim]{text:<{width}}[/]"

    # If season is provided, show only that season
    if season is not None:
        params = {"apikey": API_KEY, "i": imdb_id, "season": season}
        response = requests.get(BASE_URL, params=params).json()
        if response["Response"] == "True" and "Episodes" in response:
            episodes = response["Episodes"]
            boxes = []
            for ep in episodes:
                if ep["imdbRating"] != "N/A":
                    try:
                        ep_num = int(ep["Episode"])
                        rating = float(ep["imdbRating"])
                        color = get_color(rating)
                        box = format_box(f"Ep {ep_num}: {rating:.3f}", color)
                    except Exception:
                        box = format_box("Ep --: N/A")
                else:
                    box = format_box(f"Ep {ep['Episode']}: N/A")
                boxes.append(box)
            console.print(
                f"[bold yellow]{response['Title']} - Season {season} Rating Distribution[/]"
            )
            for b in boxes:
                console.print(b)
        else:
            console.print("[bold red]No ratings found![/]")
        return

    # If no season is provided, show all seasons in columns
    params = {"apikey": API_KEY, "i": imdb_id}
    response = requests.get(BASE_URL, params=params).json()
    if response["Response"] != "True" or response.get("Type") != "series":
        console.print("[bold red]Series not found![/]")
        return
    try:
        total_seasons = int(response["totalSeasons"])
    except Exception:
        console.print("[bold red]Could not determine total seasons![/]")
        return
    title = response["Title"]

    all_season_boxes = []  # List of lists, each inner list is a season's boxes
    season_averages = []
    max_episodes = 0
    for s in range(1, total_seasons + 1):
        params = {"apikey": API_KEY, "i": imdb_id, "season": s}
        resp = requests.get(BASE_URL, params=params).json()
        if resp["Response"] == "True" and "Episodes" in resp:
            episodes = resp["Episodes"]
            season_boxes = []
            ratings = []
            for ep in episodes:
                if ep["imdbRating"] != "N/A":
                    try:
                        ep_num = int(ep["Episode"])
                        rating = float(ep["imdbRating"])
                        color = get_color(rating)
                        box = format_box(f"Ep {ep_num}: {rating:.3f}", color)
                        ratings.append(rating)
                    except Exception:
                        box = format_box(f"Ep --: N/A")
                else:
                    box = format_box(f"Ep {ep['Episode']}: N/A")
                season_boxes.append(box)
            all_season_boxes.append(season_boxes)
            if len(season_boxes) > max_episodes:
                max_episodes = len(season_boxes)
            if ratings:
                avg = sum(ratings) / len(ratings)
                season_averages.append(avg)
            else:
                season_averages.append(None)
        else:
            all_season_boxes.append([format_box("Ep --: N/A")])
            season_averages.append(None)

    box_width = 15
    header = "  ".join(
        [
            f"[bold underline]{('Season ' + str(s) + (f' ({season_averages[s-1]:.2f})' if season_averages[s-1] is not None else ' (N/A)')):<{box_width}}[/]"
            for s in range(1, total_seasons + 1)
        ]
    )
    console.print(f"[bold yellow]{title} - All Seasons Rating Distribution[/]")
    console.print(header)

    for ep_idx in range(max_episodes):
        row = []
        for season_boxes in all_season_boxes:
            if ep_idx < len(season_boxes):
                row.append(season_boxes[ep_idx])
            else:
                row.append(format_box("", width=15))
        console.print("  ".join(row))


if __name__ == "__main__":
    cli()
