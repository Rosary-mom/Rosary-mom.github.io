"""Generate charts for rosary.health blog: Bio vs Tech Hybrid Resilience."""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.gridspec as gridspec

OUT = os.path.join(os.path.dirname(__file__), "blog-assets", "hybride-resilienz")
os.makedirs(OUT, exist_ok=True)

# Dark/gold palette matching Magnifica Humanitas blog
BG = "#05080F"
PANEL = "#0A0F1C"
GOLD = "#C9A227"
GOLD_LIGHT = "#E8D5A3"
GREEN = "#2D6A4F"
GREEN_LIGHT = "#52B788"
BLUE = "#1B4965"
BLUE_LIGHT = "#5FA8D3"
TEXT = "#EDE4D3"
MUTED = "#A89B7F"
GRID = "#2A2F3D"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": PANEL,
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT,
    "text.color": TEXT,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "grid.color": GRID,
    "grid.alpha": 0.4,
    "font.family": "serif",
    "font.size": 10,
})


def years_2000_2026():
    return np.arange(2000, 2027)


def interpolate_market(years, anchors):
    """Linear interpolation between anchor dict {year: value}."""
    ax_years = sorted(anchors.keys())
    ax_vals = [anchors[y] for y in ax_years]
    return np.interp(years, ax_years, ax_vals)


def annual_sales_global():
    years = years_2000_2026()
    anchors = {2000: 18, 2005: 28, 2010: 45, 2015: 75, 2020: 120, 2023: 136 / 0.92,
               2024: 145 / 0.92, 2025: 168, 2026: 185}
    return years, interpolate_market(years, anchors)


def annual_sales_usa():
    years = years_2000_2026()
    anchors = {2000: 8, 2005: 12, 2010: 20, 2015: 35, 2020: 52, 2024: 68, 2025: 76.6, 2026: 76}
    return years, interpolate_market(years, anchors)


def annual_sales_de():
    years = years_2000_2026()
    # EUR values; DM conversion pre-2000 handled in narrative
    anchors = {2000: 2.1, 2005: 3.2, 2010: 5.0, 2015: 8.5, 2020: 12.5, 2024: 17.0, 2026: 19.5}
    return years, interpolate_market(years, anchors)


def cumulative_simple(annual):
    return np.cumsum(annual)


def cumulative_compound(annual, rate=0.05):
    n = len(annual)
    result = np.zeros(n)
    for i in range(n):
        total = 0.0
        for j in range(i + 1):
            years_elapsed = i - j
            total += annual[j] * ((1 + rate) ** years_elapsed)
        result[i] = total
    return result


def chart_market_trends():
    years, g = annual_sales_global()
    _, u = annual_sales_usa()
    _, d = annual_sales_de()

    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.plot(years, g, color=GREEN_LIGHT, linewidth=2.5, label="Global (Mrd. USD)")
    ax.plot(years, u, color=GOLD, linewidth=2.5, label="USA (Mrd. USD)")
    ax.plot(years, d, color=BLUE_LIGHT, linewidth=2.5, label="Deutschland (Mrd. EUR)")

    milestones = [(1992, "EG-Ökoverordnung"), (2001, "Biosiegel DE/EU"), (2010, "Cult Food / Mainstream")]
    for yr, label in milestones:
        ax.axvline(yr, color=MUTED, linestyle="--", alpha=0.55, linewidth=1)
        ax.text(yr + 0.3, ax.get_ylim()[1] * 0.92 if ax.get_ylim()[1] else 170, label,
                rotation=90, va="top", fontsize=8, color=MUTED)

    ax.set_title("Ökonomischer Mehrwert des Bio-Sektors (Proxy: Retail Sales)", fontsize=14, color=GOLD, pad=14)
    ax.set_xlabel("Jahr")
    ax.set_ylabel("Marktgröße (Retail Sales)")
    ax.legend(loc="upper left", framealpha=0.3)
    ax.grid(True, linestyle="-", alpha=0.25)
    ax.set_xlim(1990, 2026)

    note = ("Approximative Werte (FiBL, OTA, AMI/Statista). Währungen nicht umgerechnet.\n"
            "Projektionen 2025/26: CAGR 8–13 % je nach Region.")
    fig.text(0.12, 0.02, note, fontsize=8, color=MUTED)

    fig.savefig(os.path.join(OUT, "01-bio-marktgroesse-1992-2026.png"), dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def chart_cumulative_curves():
    years, g = annual_sales_global()
    _, u = annual_sales_usa()
    _, d = annual_sales_de()

    cum_g = cumulative_simple(g)
    cum_u = cumulative_simple(u)
    cum_d = cumulative_simple(d)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax, data, labels, title in [
        (axes[0], (cum_g, cum_u, cum_d), ("Global", "USA", "Deutschland"), "Einfache Summenkurve (kumuliert)"),
        (axes[1],
         (cumulative_compound(g), cumulative_compound(u), cumulative_compound(d)),
         ("Global", "USA", "Deutschland"),
         "Summenkurve mit Zinseszinseffekt (5 % p.a.)"),
    ]:
        colors = [GREEN_LIGHT, GOLD, BLUE_LIGHT]
        for series, lbl, col in zip(data, labels, colors):
            ax.plot(years, series, linewidth=2.5, label=lbl, color=col)
        ax.set_title(title, fontsize=12, color=GOLD)
        ax.set_xlabel("Jahr")
        ax.set_ylabel("Kumulierter Wert (Mrd.)")
        ax.legend(framealpha=0.3)
        ax.grid(True, alpha=0.25)

    fig.suptitle("Kumulierter ökonomischer Mehrwert seit 2000", fontsize=14, color=TEXT, y=1.02)
    fig.text(0.12, -0.02,
             "2026: Global einfach ~2.170 Mrd. USD | mit 5 % Zinseszins ~3.464 Mrd. USD. "
             "DE-Werte in EUR (Euro ab 1999/2002, 1 EUR = 1,95583 DM).",
             fontsize=8, color=MUTED)
    fig.savefig(os.path.join(OUT, "02-kumulierte-summen-zinseszins.png"), dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def chart_three_comparisons():
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.5))

    # 1. Area
    ax = axes[0]
    labels = ["Bio\n(organisch)", "Musk\n(Tesla+SpaceX)"]
    vals = [99_000_000, 50_000]  # ha
    bars = ax.bar(labels, vals, color=[GREEN, BLUE_LIGHT], width=0.55)
    ax.set_yscale("log")
    ax.set_ylabel("Hektar (log-Skala)")
    ax.set_title("Fläche", color=GOLD, fontsize=12)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.15, f"{v:,.0f} ha", ha="center", fontsize=9, color=TEXT)

    # 2. People
    ax = axes[1]
    labels = ["Bio-Produzenten", "Tesla+SpaceX\nMitarbeiter"]
    vals = [4_800_000, 160_000]
    bars = ax.bar(labels, vals, color=[GREEN, BLUE_LIGHT], width=0.55)
    ax.set_ylabel("Personen")
    ax.set_title("Lebensunterhalt", color=GOLD, fontsize=12)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 80000, f"{v/1e6:.1f} Mio." if v > 1e6 else f"{v:,}",
                ha="center", fontsize=9, color=TEXT)

    # 3. Intergenerational
    ax = axes[2]
    x = np.arange(2)
    width = 0.35
    bio = [900, 1500]
    musk = [400, 600]
    ax.bar(x - width / 2, bio, width, label="Bio (Grün)", color=GREEN)
    ax.bar(x + width / 2, musk, width, label="Musk (Schwarz-Blau)", color=BLUE)
    ax.set_xticks(x)
    ax.set_xticklabels(["Gen 1\n(2000–2020 / 2010–2030)", "Gen 2\n(2020–2040)"])
    ax.set_ylabel("Kumulativer Effekt (Mrd. USD)")
    ax.set_title("Intergenerationell", color=GOLD, fontsize=12)
    ax.legend(framealpha=0.3, fontsize=8)

    fig.suptitle("Bodenständiger Vergleich: Bio-Agenda vs. Musk-Agenda", fontsize=14, color=TEXT, y=1.02)
    fig.text(0.1, -0.04, "Quellen: FiBL 2024/26 (Bio), Tesla/SpaceX Unternehmensberichte (Musk). Approximative Modelle.",
             fontsize=8, color=MUTED)
    fig.savefig(os.path.join(OUT, "03-vergleich-flaeche-menschen-generationen.png"), dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def chart_action_diagram():
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def box(x, y, w, h, text, color, alpha=0.85):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.2",
                              facecolor=color, edgecolor=GOLD, alpha=alpha, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, color=TEXT, wrap=True)

    # Left path - Bio
    ax.text(2.5, 9.3, "BIO-AGENDA (Grün)", ha="center", fontsize=13, color=GREEN_LIGHT, fontweight="bold")
    box(0.5, 7.5, 4, 1.2, "Input: EG-Öko 1991/92\nBiosiegel, USDA Organic\nLabeling & Branding", GREEN, 0.7)
    box(0.5, 5.8, 4, 1.2, "Output: ~99 Mio. ha\n~4,8 Mio. Produzenten\nRetail Sales ↑↑", GREEN, 0.55)
    box(0.5, 4.1, 4, 1.2, "Natürliches Kapital:\nBoden, Biodiversität\nErnährungssicherheit", GREEN, 0.45)

    # Right path - Musk
    ax.text(7.5, 9.3, "MUSK-AGENDA (Schwarz-Blau)", ha="center", fontsize=13, color=BLUE_LIGHT, fontweight="bold")
    box(5.5, 7.5, 4, 1.2, "Input: EV, Solar, Starlink\nSpaceX IPO 2026\nRaumfahrt-Innovation", BLUE, 0.7)
    box(5.5, 5.8, 4, 1.2, "Output: ~160k Jobs\nKonzentrierte Wertschöpfung\nTech-Transfer", BLUE, 0.55)
    box(5.5, 4.1, 4, 1.2, "Technologisches Kapital:\nDekarbonisierung\nBackup-Strategien (Mars)", BLUE, 0.45)

    # Center synthesis
    box(2.5, 1.8, 5, 1.5,
        "HYBRIDE RESILIENZ-STRATEGIE\nRegenerative Erde + Technologische Beschleunigung\n"
        "→ max. intergenerationeller Transfer (3S: Sozial, Ökonomisch, Ökologisch)",
        "#5C1A2E", 0.9)

    # Arrows
    for sx, sy, ex, ey in [(2.5, 7.5, 2.5, 7.0), (2.5, 5.8, 2.5, 5.3), (2.5, 4.1, 3.5, 3.3),
                             (7.5, 7.5, 7.5, 7.0), (7.5, 5.8, 7.5, 5.3), (7.5, 4.1, 6.5, 3.3)]:
        ax.annotate("", xy=(ex, ey), xytext=(sx, sy),
                    arrowprops=dict(arrowstyle="->", color=GOLD, lw=1.8))

    ax.text(5, 0.6, "Hypothese Juni 2026: Unter Last (Klima, Bevölkerung, Ressourcen) reicht keine Agenda allein.",
            ha="center", fontsize=9, color=MUTED, style="italic")

    fig.savefig(os.path.join(OUT, "04-handlungsdiagramm-hybride-resilienz.png"), dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def chart_space_agriculture():
    fig, ax = plt.subplots(figsize=(12, 5))
    phases = ["2026\nSpaceX IPO", "2030\nR&D", "2035\nPrototypen", "2040\nErnte", "2050+\nMars-Farm"]
    x = np.arange(len(phases))
    risk = [30, 45, 60, 75, 90]
    return_est = [8, 10, 15, 22, 30]

    ax2 = ax.twinx()
    ax.bar(x - 0.2, risk, 0.4, label="Risiko-Index", color="#5C1A2E", alpha=0.8)
    ax2.plot(x + 0.2, return_est, "o-", color=GOLD, linewidth=2.5, markersize=8, label="Erw. IRR (%)")

    ax.set_xticks(x)
    ax.set_xticklabels(phases)
    ax.set_ylabel("Risiko (illustrativ)", color=MUTED)
    ax2.set_ylabel("Erwartete Rendite IRR %", color=GOLD)
    ax.set_title("Space Agriculture – Spekulatives Szenario (≥20 Jahre)", fontsize=13, color=GOLD, pad=12)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left", framealpha=0.3)

    fig.text(0.1, 0.02,
             "Bonds 12–25 %, Futures Astro-Produce. Keine Finanzberatung. Illustrative Annahmen.",
             fontsize=8, color=MUTED)
    fig.savefig(os.path.join(OUT, "05-space-agriculture-spekulativ.png"), dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def chart_investment_universe():
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")

    investments = {
        "Bio (Earth)": (12, 9, 9, GREEN),
        "SpaceX 2026": (18, 6, 7, BLUE_LIGHT),
        "Space Ag Bull": (35, 7, 8, "#40E0D0"),
        "Space Ag Base": (16, 6, 7, GOLD),
        "Space Ag Bear": (4, 4, 5, "#8B0000"),
    }

    for name, (irr, social, eco, col) in investments.items():
        ax.scatter(irr, social, eco, s=180, c=col, edgecolors=GOLD, linewidths=1, depthshade=True)
        ax.text(irr, social, eco + 0.3, name, fontsize=8, color=TEXT)

    ax.plot([18, 35], [6, 7], [7, 8], "--", color=MUTED, alpha=0.5)
    ax.plot([18, 16], [6, 6], [7, 7], "--", color=MUTED, alpha=0.5)
    ax.plot([18, 4], [6, 4], [7, 5], "--", color=MUTED, alpha=0.5)

    ax.set_xlabel("Ökonomisch: IRR %")
    ax.set_ylabel("Sozial (0–10)")
    ax.set_zlabel("Ökologisch (0–10)")
    ax.set_title("Anlageuniversum „Grüner Mars“\n3S-Formel + Value/Risk", fontsize=13, color=GOLD, pad=20)
    ax.set_facecolor(PANEL)
    fig.patch.set_facecolor(BG)

    fig.text(0.08, 0.02,
             "Hybride Allokation: 60–70 % Bio/regenerativ + 30–40 % SpaceX/Space-Ag. Spekulativ, keine Beratung.",
             fontsize=8, color=MUTED)
    fig.savefig(os.path.join(OUT, "06-anlageuniversum-gruener-mars-3d.png"), dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def chart_musk_wealth_comparison():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    categories = ["Musk Vermögen\n(Juni 2026)", "Bio kumuliert\neinfach", "Bio kumuliert\n5% Zinseszins"]
    values = [1100, 2170, 3464]
    colors = [BLUE_LIGHT, GREEN, GREEN_LIGHT]
    bars = ax.barh(categories, values, color=colors, height=0.55)
    ax.set_xlabel("Mrd. USD (Größenordnung)")
    ax.set_title("Größenordnungsvergleich: Kollektiver Bio-Impact vs. Musk-Vermögen", fontsize=12, color=GOLD)
    for b, v in zip(bars, values):
        ax.text(v + 50, b.get_y() + b.get_height() / 2, f"{v:,}".replace(",", "."), va="center", color=TEXT)
    ax.grid(True, axis="x", alpha=0.25)
    fig.text(0.1, 0.02, "Musk: Forbes/Bloomberg ~1,1 Bio. USD nach SpaceX-IPO (12.06.2026). Bio: Retail-Sales-Proxy.",
             fontsize=8, color=MUTED)
    fig.savefig(os.path.join(OUT, "07-groessenordnung-musk-vs-bio.png"), dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    chart_market_trends()
    chart_cumulative_curves()
    chart_three_comparisons()
    chart_action_diagram()
    chart_space_agriculture()
    chart_investment_universe()
    chart_musk_wealth_comparison()
    print(f"Charts saved to {OUT}")