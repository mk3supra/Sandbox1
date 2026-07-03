#!/usr/bin/env python3
"""
Product Availability Checker
Run `python main.py --help` to get started.
"""

import sys
import time
from datetime import datetime
from typing import List, Union

import click
import schedule
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import config
import notifier
import runner
from models import CheckResult, EventProduct, PhysicalProduct

console = Console()

VALID_PHYSICAL_SITES = ["amazon", "walmart", "bestbuy"]
VALID_EVENT_SITES = ["seatgeek", "stubhub"]


# ── display helpers ────────────────────────────────────────────────────────────

def _price(p) -> str:
    return f"${p:.2f}" if p is not None else "—"


def display_results(product: Union[PhysicalProduct, EventProduct],
                    results: List[CheckResult]) -> bool:
    """Render a panel with per-site results. Returns True if anything is available."""
    has_available = any(r.available for r in results)

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim")
    table.add_column("Site", style="cyan", min_width=10)
    table.add_column("Status", min_width=16)
    table.add_column("Price", min_width=9, justify="right")
    table.add_column("Details")

    for result in sorted(results, key=lambda r: r.site):
        if result.error:
            status = Text("⚠  Error", style="yellow")
            price_str = Text("—")
        elif result.available:
            status = Text("✓  Available", style="bold green")
            price_str = Text(_price(result.price), style="green")
        else:
            status = Text("✗  Unavailable", style="dim red")
            price_str = Text("—", style="dim")

        details = result.message
        if result.available and result.url:
            details += f"\n[link={result.url}][dim]{result.url[:60]}[/dim][/link]"

        table.add_row(result.site, status, price_str, details)

    border = "green" if has_available else "red"
    flag = "[bold green]AVAILABLE[/bold green]" if has_available else "[dim red]Not Available[/dim red]"
    panel = Panel(
        table,
        title=f" {product.name}  —  {flag} ",
        border_style=border,
    )
    console.print(panel)
    return has_available


def _run_check() -> bool:
    products = config.get_products()
    if not products:
        console.print("[yellow]No products configured. Use 'add-product' or 'add-event' to add some.[/yellow]")
        return False

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.rule(f"[bold]Checking {len(products)} item(s)  •  {ts}[/bold]")

    found_any = False
    for product, results in runner.run_all_checks(products):
        has = display_results(product, results)
        if has:
            found_any = True
            for r in results:
                if r.available:
                    notifier.notify_available(product.name, r)

    if found_any:
        console.print("\n[bold green]Items found! Check the links above.[/bold green]")
    else:
        console.print("\n[dim]Nothing in stock right now.[/dim]")

    return found_any


# ── CLI commands ───────────────────────────────────────────────────────────────

@click.group()
def cli():
    """
    \b
    Product Availability Checker
    ════════════════════════════
    Monitor physical products (Amazon, Walmart, Best Buy) and
    event tickets (SeatGeek, StubHub) — get notified the moment
    something becomes available.

    Quick start:
      python main.py add-product --name "PlayStation 5" --search "PlayStation 5 console"
      python main.py add-event   --name "Cowboys Game"  --search "Dallas Cowboys"
      python main.py monitor
    """


@cli.command("add-product")
@click.option("--name", required=True, help="Friendly name, e.g. 'PlayStation 5'")
@click.option("--search", required=True, help="Search term to use on each site")
@click.option("--sites", default="amazon,walmart,bestbuy", show_default=True,
              help="Comma-separated list of sites")
@click.option("--max-price", type=float, default=None,
              help="Skip results above this price")
def add_product(name, search, sites, max_price):
    """Add a physical product to watch (Amazon, Walmart, Best Buy)."""
    site_list = [s.strip().lower() for s in sites.split(",") if s.strip()]
    bad = [s for s in site_list if s not in VALID_PHYSICAL_SITES]
    if bad:
        console.print(f"[red]Unknown site(s): {bad}[/red]  valid: {VALID_PHYSICAL_SITES}")
        sys.exit(1)

    product = PhysicalProduct(name=name, search_term=search, sites=site_list,
                              max_price=max_price)
    config.add_product(product)
    console.print(f"[green]Added[/green] [bold]{name}[/bold]  (id: {product.id})")
    if max_price:
        console.print(f"  max price: [cyan]${max_price:.2f}[/cyan]")
    console.print(f"  sites: [cyan]{', '.join(site_list)}[/cyan]")


@cli.command("add-event")
@click.option("--name", required=True, help="Friendly name, e.g. 'Dallas Cowboys'")
@click.option("--search", required=True, help="Search term to use on ticket sites")
@click.option("--sites", default="seatgeek,stubhub", show_default=True,
              help="Comma-separated list of ticket sites")
@click.option("--max-price", type=float, default=None,
              help="Skip tickets priced above this")
@click.option("--date-start", default=None, metavar="YYYY-MM-DD",
              help="Only show events on or after this date")
@click.option("--date-end", default=None, metavar="YYYY-MM-DD",
              help="Only show events on or before this date")
def add_event(name, search, sites, max_price, date_start, date_end):
    """Add an event to watch for tickets (SeatGeek, StubHub)."""
    site_list = [s.strip().lower() for s in sites.split(",") if s.strip()]
    bad = [s for s in site_list if s not in VALID_EVENT_SITES]
    if bad:
        console.print(f"[red]Unknown site(s): {bad}[/red]  valid: {VALID_EVENT_SITES}")
        sys.exit(1)

    event = EventProduct(
        name=name, search_term=search, sites=site_list,
        max_price=max_price, date_start=date_start, date_end=date_end,
    )
    config.add_product(event)
    console.print(f"[green]Added[/green] [bold]{name}[/bold]  (id: {event.id})")
    if max_price:
        console.print(f"  max price: [cyan]${max_price:.2f}[/cyan]")
    if date_start or date_end:
        console.print(f"  date range: [cyan]{date_start or '…'} → {date_end or '…'}[/cyan]")
    console.print(f"  sites: [cyan]{', '.join(site_list)}[/cyan]")


@cli.command("list")
def list_products():
    """List all products and events currently being watched."""
    products = config.get_products()
    if not products:
        console.print("[yellow]Nothing configured yet.[/yellow]")
        console.print("Use [bold]add-product[/bold] or [bold]add-event[/bold] to add items.")
        return

    table = Table(title="Watched Items", box=box.ROUNDED)
    table.add_column("ID", style="dim", min_width=8)
    table.add_column("Name", style="bold cyan")
    table.add_column("Type")
    table.add_column("Search Term")
    table.add_column("Sites")
    table.add_column("Max Price", justify="right")
    table.add_column("Date Range")

    for p in products:
        if isinstance(p, PhysicalProduct):
            type_label = "[blue]Physical[/blue]"
            date_range = "—"
        else:
            type_label = "[magenta]Event[/magenta]"
            parts = []
            if p.date_start:
                parts.append(p.date_start)
            if p.date_end:
                parts.append(p.date_end)
            date_range = " → ".join(parts) if parts else "—"

        price_str = f"${p.max_price:.2f}" if p.max_price else "Any"
        table.add_row(
            p.id, p.name, type_label, p.search_term,
            ", ".join(p.sites), price_str, date_range,
        )

    console.print(table)


@cli.command("remove")
@click.argument("product_id")
def remove_product(product_id):
    """Remove a watched item by its ID (shown in 'list')."""
    if config.remove_product(product_id):
        console.print(f"[green]Removed[/green] {product_id}")
    else:
        console.print(f"[red]Not found:[/red] {product_id}")
        sys.exit(1)


@cli.command("check")
def check_once():
    """Run a single availability check right now."""
    _run_check()


@cli.command("monitor")
@click.option("--interval", default=30, show_default=True,
              help="How often to check, in minutes")
def monitor(interval):
    """
    Check continuously on a schedule.

    Runs an immediate check, then repeats every INTERVAL minutes.
    Press Ctrl+C to stop.
    """
    console.print(
        f"[bold green]Monitor started[/bold green] — "
        f"checking every [cyan]{interval}[/cyan] minute(s). "
        "Press [bold]Ctrl+C[/bold] to stop.\n"
    )

    _run_check()
    schedule.every(interval).minutes.do(_run_check)

    try:
        while True:
            schedule.run_pending()
            time.sleep(15)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")


if __name__ == "__main__":
    cli()
