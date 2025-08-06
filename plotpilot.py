import os
import click
import requests
from rich.console import Console
from rich.text import Text
from rich.layout import Layout
from rich.table import Table
import shutil
import io
from dotenv import load_dotenv

try:
    from PIL import Image
    from img2unicode import Renderer
except ImportError:
    Image = None
    Renderer = None

load_dotenv()

console = Console()

API_KEY = os.getenv("OMDB_API_KEY")
BASE_URL = "https://www.omdbapi.com/"


@click.group()
def cli():
    """PlotPilot: Explore movie and series data in your terminal."""
    pass


@cli.command()
@click.argument("title")
def search(title):
    """Search for a movie or series by title and display detailed information with poster."""
    if Image is None or Renderer is None:
        console.print(
            "[bold yellow]Warning: PIL or img2unicode not installed. Poster image will not be displayed.[/]"
        )

    params = {"apikey": API_KEY, "t": title}
    response = requests.get(BASE_URL, params=params).json()

    if response["Response"] == "True":
        t = response["Type"]

        text_info = Text()

        title = response.get("Title", "N/A")
        year = response.get("Year", "N/A")
        genre = response.get("Genre", "N/A")
        runtime = response.get("Runtime", "N/A")
        language = response.get("Language", "N/A")
        country = response.get("Country", "N/A")
        awards = response.get("Awards", "N/A")
        plot = response.get("Plot", "N/A")
        imdb_id = response.get("imdbID", "N/A")
        imdb_rating = response.get("imdbRating", "N/A")
        imdb_votes = response.get("imdbVotes", "N/A")
        ratings = response.get("Ratings", [])
        actors = response.get("Actors", "N/A")
        writer = response.get("Writer", "N/A")

        text_info.append(f"{title} ({year})\n", style="bold green")
        text_info.append(f"Genre: {genre}\n", style="bold")
        text_info.append(f"Runtime: {runtime}\n", style="bold")
        text_info.append(f"Language: {language}\n", style="bold")
        text_info.append(f"Country: {country}\n", style="bold")
        text_info.append(f"Writer: {writer}\n", style="bold")
        text_info.append(f"Actors: {actors}\n", style="bold")
        text_info.append(f"IMDb ID: {imdb_id}\n", style="bold")
        text_info.append(
            f"IMDb Rating: {imdb_rating} ({imdb_votes} votes)\n", style="bold"
        )
        text_info.append(f"Awards: {awards}\n", style="bold")

        if t == "movie":
            director = response.get("Director", "N/A")
            box_office = response.get("BoxOffice", "N/A")
            metascore = response.get("Metascore", "N/A")
            text_info.append(f"Director: {director}\n", style="bold")
            text_info.append(f"Metascore: {metascore}\n", style="bold")
            text_info.append(f"Box Office: {box_office}\n", style="bold")
        elif t == "series":
            total_seasons = response.get("totalSeasons", "N/A")
            text_info.append(f"Total Seasons: {total_seasons}\n", style="bold")

        if ratings:
            text_info.append("Ratings:\n", style="bold")
            for rating in ratings:
                text_info.append(
                    f"• {rating['Source']}: {rating['Value']}\n", style="cyan"
                )
        text_info.append(f"\nPlot: {plot}\n", style="bold")

        # Handle poster image
        poster_url = response.get("Poster", "N/A")
        image_text = None
        if poster_url != "N/A" and Image is not None and Renderer is not None:
            try:
                response = requests.get(poster_url)
                response.raise_for_status()  # Check for HTTP errors
                image_data = io.BytesIO(response.content)
                image = Image.open(image_data)
                renderer = Renderer()
                image_str = renderer.render_terminal(image)  # FIXME
                image_text = Text.from_ansi(image_str)
            except Exception as e:
                console.print(f"[bold yellow]Could not display poster: {e}[/]")

        terminal_width = shutil.get_terminal_size().columns
        if terminal_width > 100 and image_text is not None:
            # Side-by-side layout
            layout = Layout()
            layout.split_row(
                Layout(name="left"),
                Layout(name="right", size=40),
            )
            layout["left"].update(text_info)
            layout["right"].update(image_text)
            console.print(layout)
        else:
            # Vertical layout (text above image or text only)
            console.print(text_info)
            if image_text is not None:
                console.print(image_text)
    else:
        console.print("[bold red]Title not found![/]")


@cli.command()
@click.argument("imdb_id")
def synopsis(imdb_id):
    """Fetch the full synopsis for a movie or series."""
    params = {"apikey": API_KEY, "t": imdb_id, "plot": "full"}
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
    params = {"apikey": API_KEY, "t": imdb_id, "season": season}
    response = requests.get(BASE_URL, params=params).json()
    if response["Response"] == "True" and "Episodes" in response:
        table = Table(title=f"{response.get('Title', 'N/A')} - Season {season}")
        table.add_column("Episode", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Released", style="yellow")
        table.add_column("Rating", style="green")
        table.add_column("IMDb ID", style="blue")
        table.add_column("Summary", style="white")
        for ep in response["Episodes"]:
            episode_num = ep.get("Episode", "N/A")
            title = ep.get("Title", "N/A")
            released = ep.get("Released", "N/A")
            rating = ep.get("imdbRating", "N/A")
            ep_imdb_id = ep.get("imdbID", "N/A")
            summary = "N/A"
            if ep_imdb_id != "N/A":
                detail_params = {"apikey": API_KEY, "i": ep_imdb_id, "plot": "full"}
                detail_resp = requests.get(BASE_URL, params=detail_params).json()
                summary = detail_resp.get("Plot", "N/A")
            table.add_row(
                str(episode_num), title, released, rating, ep_imdb_id, summary
            )
        console.print(table)
    else:
        console.print("[bold red]No episodes found![/]")


@cli.command()
@click.argument("imdb_id")
@click.option(
    "--season", default=None, type=int, help="Season number (if omitted, show all)"
)
def ratings(imdb_id, season):
    """Visualize episode rating distribution for a series."""

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

    if season is not None:
        params = {"apikey": API_KEY, "t": imdb_id, "season": season}
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

    params = {"apikey": API_KEY, "t": imdb_id}
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

    all_season_boxes = []
    season_averages = []
    max_episodes = 0
    for s in range(1, total_seasons + 1):
        params = {"apikey": API_KEY, "t": imdb_id, "season": s}
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
                        box = format_box("Ep --: N/A")
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
