"""
Plotting utilities for NVCL spectral summary reports.

Provides functions for creating stacked bar plots of mineral/group classifications,
page headers for PDF reports, and composite spectral summary panels.
"""

import logging
import os
import sys
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from matplotlib.axes import Axes
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
import matplotlib.image as mpimg
import matplotlib.lines as mlines
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator
from matplotlib import colormaps as cm
from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

try:
    import colorcet as cc
except ImportError:  # pragma: no cover
    cc = None

# Set up debugging
LOG_LVL = logging.INFO
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(LOG_LVL)

if not LOGGER.hasHandlers():
    # Create logging console handler
    HANDLER = logging.StreamHandler(sys.stdout)

    # Create logging formatter
    FORMATTER = logging.Formatter(
        "%(name)s -- %(levelname)s - %(funcName)s: %(message)s"
    )

    # Add formatter to ch
    HANDLER.setFormatter(FORMATTER)

    # Add handler to LOGGER and set level
    LOGGER.addHandler(HANDLER)


def _tick_top(ax: Axes, also_label_bottom: bool = True) -> None:
    """
    Move x-axis ticks and labels to the top of the given axes.

    :param Axes ax: matplotlib axes instance
    :param bool also_label_bottom: whether to keep bottom labels. Defaults to True.
    """
    ax.tick_params(
        top=True,
        which="both",
        labeltop=True,
        labelbottom=also_label_bottom,
        labelsize=8,
    )
    ax.tick_params(axis="x", which="major", labelsize=8, labelrotation=90)
    ax.xaxis.set_label_position("top")
    ax.axes.xaxis.set_major_locator(MultipleLocator(20))
    ax.axes.xaxis.set_minor_locator(MultipleLocator(10))


def draw_stacked_bar(
    ax: Axes,
    df,
    *,
    y: str = "StartDepth",
    cols: Optional[List[str]] = None,
    height: float = 1.0,
    colours: Optional[Dict[str, tuple]] = None,
    sort: bool = True,
    yticks: bool = True,
    major_locator: int = 20,
    minor_locator: int = 4,
) -> Dict[str, Patch]:
    """
    Draw a horizontal stacked bar plot of mineral/group classifications on the given axes.

    Each column in *cols* is rendered as a segment of a horizontal bar whose total width
    represents 100% spectral contribution at a given depth.

    :param Axes ax: matplotlib axes to draw on
    :param pd.DataFrame df: DataFrame containing depth and classification columns
    :param str y: column name for the y-axis (depth) values. Defaults to ``"StartDepth"``.
    :param Optional[List[str]] cols: columns to plot. If ``None``, all columns from the 6th
        onward are used.
    :param float height: height of each bar in depth units. Defaults to ``1.0``.
    :param Optional[Dict[str, tuple]] colours: mapping of column name to RGBA colour tuple.
        If ``None``, a ``colorcet`` categorical palette is used.
    :param bool sort: sort columns by total sum descending before plotting. Defaults to ``True``.
    :param bool yticks: whether to configure y-axis major/minor ticks. Defaults to ``True``.
    :param int major_locator: major tick interval in depth units. Defaults to ``20``.
    :param int minor_locator: minor tick interval in depth units. Defaults to ``4``.

    :return: dictionary mapping column names to legend ``Patch`` handles
    :rtype: Dict[str, Patch]
    """
    if cols is None:
        cols = list(df.columns[5:])

    if colours is None:
        if cc is None:
            raise ImportError(
                "colorcet is required for automatic colour generation. "
                "Install it or pass an explicit 'colours' mapping."
            )
        colours = dict(
            zip(cols, cc.cm.glasbey_category10(np.linspace(0, 1, len(cols))))
        )

    y_vals = df[y].values
    lefts = np.zeros(len(df))

    if sort:
        col_sums = df[cols].sum().sort_values(ascending=False)
        cols = col_sums.index.tolist()

    for col in cols:
        ax.barh(
            y_vals,
            df[col].values,
            left=lefts,
            height=height,
            color=colours[col],
            align="center",
        )
        lefts += df[col].values

    if yticks:
        ax.axes.yaxis.set_major_locator(MultipleLocator(major_locator))
        ax.axes.yaxis.set_minor_locator(MultipleLocator(minor_locator))

    handles = {col: Patch(facecolor=colours[col], label=col) for col in cols}
    return handles


def page_header(
    ax: Axes,
    boreholeid: str,
    *,
    name: Optional[str] = None,
    year_drilled: Optional[str] = None,
    drill_type: Optional[str] = None,
    total_depth: Optional[str] = None,
    longitude: Optional[float] = None,
    latitude: Optional[float] = None,
    crs: Optional[str] = None,
) -> None:
    """
    Render a report page header on the given axes.

    The header includes borehole identification information and a title line.

    :param Axes ax: matplotlib axes to draw on (will be turned off)
    :param str boreholeid: borehole identifier string
    :param Optional[str] name: display name of the borehole
    :param Optional[str] year_drilled: year the hole was drilled
    :param Optional[str] drill_type: drilling method description
    :param Optional[str] total_depth: total depth string (metres)
    :param Optional[float] longitude: longitude coordinate
    :param Optional[float] latitude: latitude coordinate
    :param Optional[str] crs: coordinate reference system label (e.g. ``"GDA94"``)
    """
    ax.axis("off")
    ax.axis([0, 10, 0, 10])

    # Line 1 - name
    if name:
        ax.text(0.1, 9.5, name, fontsize=18, fontweight="bold", ha="left", va="top")

    # Line 2 - ID, year drilled, longitude
    ax.text(0.1, 7.5, f"Borehole ID: {boreholeid}", fontsize=9, ha="left", va="top")
    if year_drilled:
        ax.text(5.5, 7.5, "Year Drilled: ", fontsize=9, ha="right", va="top")
        ax.text(5.5, 7.5, year_drilled, fontsize=9, ha="left", va="top")
    if longitude is not None:
        long_str = "Longitude"
        if crs:
            long_str += f" ({crs})"
        ax.text(9, 7.5, f"{long_str}: ", fontsize=9, ha="right", va="top")
        ax.text(9, 7.5, f"{longitude:.2f}", fontsize=9, ha="left", va="top")

    # Line 3 - drill type, total depth, latitude
    if drill_type:
        ax.text(0.1, 6.5, f"Drill type: {drill_type}", fontsize=9, ha="left", va="top")
    if total_depth:
        ax.text(5.5, 6.5, "Total Depth (m): ", fontsize=9, ha="right", va="top")
        ax.text(5.5, 6.5, total_depth, fontsize=9, ha="left", va="top")
    if latitude is not None:
        lat_str = "Latitude"
        if crs:
            lat_str += f" ({crs})"
        ax.text(9, 6.5, f"{lat_str}: ", fontsize=9, ha="right", va="top")
        ax.text(9, 6.5, f"{latitude:.2f}", fontsize=9, ha="left", va="top")

    # Separator
    ax.axhline(y=5.0, color="black", linewidth=1.0)

    # Title
    ax.text(
        5,
        3.5,
        "HyLogger\u2122 Hyperspectral Data",
        fontsize=12,
        fontweight="bold",
        ha="center",
        va="center",
    )

def plot_spectral_summary(
    ax: Axes,
    df,
    class_cols: List[str],
    *,
    colours: Optional[Dict[str, tuple]] = None,
    xlabel: Optional[str] = None,
    ax2: Optional[Axes] = None,
    error_col: Optional[str] = None,
    snr_col: Optional[str] = None,
    sharey_ax: Optional[Axes] = None,
    ylim: Optional[Tuple[float, float]] = None,
    yticks: bool = True,
    major_locator: int = 20,
    minor_locator: int = 4,
) -> Dict[str, Patch]:
    """
    Plot a spectral classification summary panel with optional error/SNR overlay.

    This function combines a stacked bar chart of classification contributions with an
    optional second axes showing error (coloured bars) and signal-to-noise ratio (line).

    :param Axes ax: primary matplotlib axes for the stacked bar chart
    :param pd.DataFrame df: DataFrame with depth and classification columns
    :param List[str] class_cols: columns representing classification groups
    :param Optional[Dict[str, tuple]] colours: colour mapping passed to :func:`draw_stacked_bar`
    :param Optional[str] xlabel: label prefix (e.g. ``"SWIR"`` or ``"TIR"``)
    :param Optional[Axes] ax2: secondary axes for error/SNR overlay
    :param Optional[str] error_col: column name for error values (used with *ax2*)
    :param Optional[str] snr_col: column name for SNR values (used with *ax2*)
    :param Optional[Axes] sharey_ax: axes to share the y-axis with
    :param Optional[Tuple[float, float]] ylim: explicit (min, max) depth limits
    :param bool yticks: whether to configure y-axis ticks on the bar chart. Defaults to ``True``.
    :param int major_locator: major tick interval in depth units. Defaults to ``20``.
    :param int minor_locator: minor tick interval in depth units. Defaults to ``4``.

    :return: dictionary mapping column names to legend ``Patch`` handles
    :rtype: Dict[str, Patch]
    """
    handles = draw_stacked_bar(
        ax, df, cols=class_cols, height=1, colours=colours, yticks=yticks, major_locator=major_locator, minor_locator=minor_locator
    )

    # Configure axes
    if sharey_ax is not None:
        ax.sharey(sharey_ax)
        ax.get_yaxis().set_visible(False)
        ax.set(xlim=(0, 100))
    else:
        ax.set(ylabel="Depth (m)", xlim=(0, 100))

    if ylim is not None:
        ax.set_ylim(ylim)

    xlabel_prefix = f"{xlabel}\n" if xlabel else ""
    ax.set_xlabel(f"{xlabel_prefix}Spectral Contrib.", fontsize=8)
    ax.invert_yaxis()

    # Optional error/SNR panel
    if ax2 is not None and error_col is not None:
        norm = plt.Normalize(df[error_col].min(), 1000)
        cmap = cm.get_cmap("rainbow")
        error_colors = cmap(norm(df[error_col].values))

        ax2.barh(
            df["StartDepth"].values,
            df[error_col].values,
            height=1,
            color=error_colors,
            align="center",
        )
        ax2.set_xlim(0, 1000)
        ax2.axes.xaxis.set_major_locator(MultipleLocator(250))

        if sharey_ax is not None:
            ax2.sharey(sharey_ax)
        else:
            ax2.sharey(ax)

        # SNR line overlay
        if snr_col is not None:
            ax2_twin = ax2.twiny()
            ax2_twin.plot(
                df[snr_col].values,
                df["StartDepth"].values,
                color="gray",
                linewidth=0.8,
            )
            ax2_twin.set_xlabel("SNR", fontsize=8)
            ax2_twin.tick_params(
                axis="x", which="major", labelsize=6, labelrotation=90
            )
            ax2_twin.get_yaxis().set_visible(False)

        ax2.set_xlabel("Error", fontsize=8)
        ax2.tick_params(axis="x", which="major", labelsize=6, labelrotation=90)
        ax2.get_yaxis().set_visible(False)

    return handles


# Default subplot mosaic layout for summary report pages.
# H = Header, A = SWIR stacked bar, B = SWIR error/SNR,
# C = TIR stacked bar, D = TIR error/SNR.
_DEFAULT_PAGE_SPEC = """
HHHHHHHH
AAABCCCD
AAABCCCD
AAABCCCD
AAABCCCD
FFFFFFFF
"""

# Default A4 page size in inches (portrait).
_A4_FIGSIZE = (8.27, 11.69)


def create_summary_page(
    boreholeid: str,
    swir_df: pd.DataFrame,
    tir_df: pd.DataFrame,
    swir_cols: List[str],
    tir_cols: List[str],
    *,
    colours: Optional[Dict[str, tuple]] = None,
    swir_scalar_set: str = "uTSAS",
    tir_scalar_set: str = "ujCLST",
    section_start: float = 0.0,
    section_end: float = 500.0,
    name: Optional[str] = None,
    year_drilled: Optional[str] = None,
    drill_type: Optional[str] = None,
    total_depth: Optional[str] = None,
    longitude: Optional[float] = None,
    latitude: Optional[float] = None,
    crs: Optional[str] = None,
    figsize: Tuple[float, float] = _A4_FIGSIZE,
    page_spec: Optional[str] = None,
    logo: Optional[str] = None,
) -> Figure:
    """
    Create a single summary report page (matplotlib Figure) for a depth section.

    The page contains a header panel with borehole metadata and two side-by-side
    spectral summary panels (SWIR and TIR) each with an accompanying error/SNR panel.

    :param str boreholeid: borehole identifier
    :param pd.DataFrame swir_df: SWIR summary DataFrame (output of ``gen_summary_dataframe``)
    :param pd.DataFrame tir_df: TIR summary DataFrame (output of ``gen_summary_dataframe``)
    :param List[str] swir_cols: classification column names present in *swir_df*
    :param List[str] tir_cols: classification column names present in *tir_df*
    :param Optional[Dict[str, tuple]] colours: colour mapping for classification names.
        If ``None``, a ``colorcet`` palette is generated automatically.
    :param str swir_scalar_set: SWIR scalar set name used to derive error/SNR column names.
        Defaults to ``"uTSAS"``.
    :param str tir_scalar_set: TIR scalar set name used to derive error/SNR column names.
        Defaults to ``"ujCLST"``.
    :param float section_start: start depth (m) of the section to render.
    :param float section_end: end depth (m) of the section to render.
    :param Optional[str] name: borehole display name for the header
    :param Optional[str] year_drilled: year drilled for the header
    :param Optional[str] drill_type: drilling method for the header
    :param Optional[str] total_depth: total depth string for the header
    :param Optional[float] longitude: longitude for the header
    :param Optional[float] latitude: latitude for the header
    :param Optional[str] crs: CRS label for the header (e.g. ``"GDA94"``)
    :param Tuple[float, float] figsize: figure size in inches. Defaults to A4 portrait.
    :param Optional[str] page_spec: subplot mosaic specification string. If ``None``, the
        default layout is used.
    :param Optional[str] logo: "NSW", "QLD", etc. If ``None``, no logo is shown.

    :return: the rendered matplotlib Figure
    :rtype: Figure
    """
    if page_spec is None:
        page_spec = _DEFAULT_PAGE_SPEC

        if logo is not None:
            # Add a logo panel to the left of the header
            page_spec = page_spec.replace("HHHHHHHH", "LHHHHHHH")

    fig, ax = plt.subplot_mosaic(page_spec, figsize=figsize, dpi=300)
    # Header
    page_header(
        ax["H"],
        boreholeid,
        name=name,
        year_drilled=year_drilled,
        drill_type=drill_type,
        total_depth=total_depth,
        longitude=longitude,
        latitude=latitude,
        crs=crs,
    )

    # Logo
    if logo is not None:
        # Shift the logo axes to the left a little
        axl_bbox = ax['L'].get_position()
        ax["L"].set_position([axl_bbox.x0-0.05, axl_bbox.y0+0.01, axl_bbox.width+0.05, axl_bbox.height])
        ax["L"].axis("off")

        _logo_path = os.path.join(os.path.dirname(__file__), "data", f"{logo.lower()}-logo.png")
        if os.path.isfile(_logo_path):
            _logo_img = mpimg.imread(_logo_path)
            logo_height = _logo_img.shape[0]
            logo_width = _logo_img.shape[1]
            logo_aspect = logo_width / logo_height
            x_min, x_max = 0, 1
            y_height = (x_max - x_min) / logo_aspect
            y_min, y_max = 1.0 - y_height, 1.0
            logo_extent = [x_min, x_max, y_min, y_max]
            ax["L"].imshow(_logo_img, aspect="equal", extent=logo_extent, origin="upper")
            ax["L"].set_xlim((0, 1))
            ax["L"].set_ylim((0, 1))
    

    ylim = (section_start, section_end)

    # Filter DataFrames to the current depth section
    swir_section = swir_df.loc[
        (swir_df["StartDepth"] >= section_start) & (swir_df["EndDepth"] <= section_end)
    ]
    tir_section = tir_df.loc[
        (tir_df["StartDepth"] >= section_start) & (tir_df["EndDepth"] <= section_end)
    ]

    # Calculate how many depth labels to show on the y-axis based on the section depth
    section_depth = section_end - section_start
    if section_depth <= 100:
        major_locator = 10
        minor_locator = 2
    elif section_depth <= 500:
        major_locator = 20
        minor_locator = 4
    elif section_depth <= 1000:
        major_locator = 50
        minor_locator = 10
    else:
        major_locator = 100
        minor_locator = 20

    # SWIR panel
    swir_error_col = f"Error_{swir_scalar_set}"
    swir_snr_col = f"SNR_{swir_scalar_set}"
    swir_handles = plot_spectral_summary(
        ax["A"],
        swir_section,
        swir_cols,
        colours=colours,
        xlabel="SWIR",
        ax2=ax["B"],
        error_col=swir_error_col,
        snr_col=swir_snr_col,
        ylim=ylim,
        major_locator=major_locator,
        minor_locator=minor_locator
    )
    ax["A"].tick_params(axis="y", labelleft=True)

    # TIR panel
    tir_error_col = f"Error_{tir_scalar_set}"
    tir_snr_col = f"SNR_{tir_scalar_set}"
    tir_handles = plot_spectral_summary(
        ax["C"],
        tir_section,
        tir_cols,
        colours=colours,
        xlabel="TIR",
        ax2=ax["D"],
        error_col=tir_error_col,
        snr_col=tir_snr_col,
        sharey_ax=ax["A"],
        ylim=ylim,
        yticks=False,
    )

    # Move x-axis ticks to top on main spectral panels
    for panel_key in "AC":
        _tick_top(ax[panel_key])

    # We put the legend in an empty axes at the bottom of the page but don't need the tick marks..
    ax["F"].axis("off")

    # SNR legend entry (bottom left of page)
    snr_line = mlines.Line2D([], [], color="gray", label="Signal to Noise Ratio (SNR)")
    snr_legend = ax["F"].legend(
        handles=[snr_line],
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(-0.05, 0.80),
        fontsize="small",
    )
    ax["F"].add_artist(snr_legend)

    # Error colorbar legend (below SNR legend)
    error_cmap = cm.get_cmap("rainbow")
    error_norm = plt.Normalize(
        vmin=0,
        vmax=1000,
    )
    sm = plt.cm.ScalarMappable(cmap=error_cmap, norm=error_norm)
    sm.set_array([])
    cbar_ax = fig.add_axes([0.1, 0.16, 0.15, 0.012])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label("Error", fontsize=9)
    cbar.ax.tick_params(labelsize=7)

    # HyLogger Spectral Groups legend (immediately to the right of SNR legend)
    all_handles: Dict[str, Patch] = {}
    all_handles.update(swir_handles)
    all_handles.update(tir_handles)
    title_fontproperties = {"weight": "bold", "size": "medium"}
    
    ax["F"].legend(
        handles=list(all_handles.values()),
        title="HyLogger\u2122 Spectral Groups",
        frameon=False,
        title_fontproperties=title_fontproperties,
        loc="upper left",
        bbox_to_anchor=(0.35, 0.80),
        ncol=4,
        fontsize="small",
        columnspacing=1.75,
        labelspacing=0.25,
        handleheight=1.5,
        handlelength=1.5,
        handletextpad=0.5,
    )

    return fig


def create_summary_report(
    boreholeid: str,
    swir_df: pd.DataFrame,
    tir_df: pd.DataFrame,
    swir_cols: List[str],
    tir_cols: List[str],
    *,
    colours: Optional[Dict[str, tuple]] = None,
    swir_scalar_set: str = "uTSAS",
    tir_scalar_set: str = "ujCLST",
    section_depth: float = 500.0,
    hole_overview: bool = False,
    output_path: Optional[Union[str, os.PathLike]] = None,
    name: Optional[str] = None,
    year_drilled: Optional[str] = None,
    drill_type: Optional[str] = None,
    total_depth: Optional[str] = None,
    longitude: Optional[float] = None,
    latitude: Optional[float] = None,
    crs: Optional[str] = None,
    figsize: Tuple[float, float] = _A4_FIGSIZE,
    page_spec: Optional[str] = None,
    pdf_metadata: Optional[Dict[str, str]] = None,
    close_figures: bool = True,
    logo: Optional[str] = None,
) -> List[Figure]:
    """
    Generate a multi-page spectral summary report.

    The borehole is divided into depth sections of *section_depth* metres.  For each
    section a page is rendered via :func:`create_summary_page`.

    When *output_path* is provided the pages are written to a PDF file.  The list of
    generated :class:`~matplotlib.figure.Figure` objects is always returned regardless
    of PDF output.

    **Example — PDF output:**

    >>> figs = create_summary_report(
    ...     "MIN_040474", swir_df, tir_df, swir_cols, tir_cols,
    ...     output_path="MIN_040474_summary.pdf",
    ... )

    **Example — figure list only (no PDF):**

    >>> figs = create_summary_report(
    ...     "MIN_040474", swir_df, tir_df, swir_cols, tir_cols,
    ...     close_figures=False,
    ... )
    >>> figs[0].show()

    :param str boreholeid: borehole identifier
    :param pd.DataFrame swir_df: SWIR summary DataFrame
    :param pd.DataFrame tir_df: TIR summary DataFrame
    :param List[str] swir_cols: SWIR classification column names
    :param List[str] tir_cols: TIR classification column names
    :param Optional[Dict[str, tuple]] colours: colour mapping for classification names
    :param str swir_scalar_set: SWIR scalar set name. Defaults to ``"uTSAS"``.
    :param str tir_scalar_set: TIR scalar set name. Defaults to ``"ujCLST"``.
    :param float section_depth: depth interval per page in metres. Defaults to ``500.0``.
    :param bool hole_overview: if ``True``, prepend a single page showing the entire
        borehole depth range before the sectioned pages. Defaults to ``False``.
    :param Optional[Union[str, os.PathLike]] output_path: path for PDF output.
        If ``None``, no PDF is written.
    :param Optional[str] name: borehole display name for the header
    :param Optional[str] year_drilled: year drilled for the header
    :param Optional[str] drill_type: drilling method for the header
    :param Optional[str] total_depth: total depth string for the header
    :param Optional[float] longitude: longitude for the header
    :param Optional[float] latitude: latitude for the header
    :param Optional[str] crs: CRS label for the header
    :param Tuple[float, float] figsize: figure size in inches. Defaults to A4 portrait.
    :param Optional[str] page_spec: subplot mosaic specification string
    :param Optional[Dict[str, str]] pdf_metadata: metadata dict for the PDF file.
        If ``None`` a sensible default is generated.
    :param bool close_figures: close each figure after saving to PDF to free memory.
        Defaults to ``True``.  Set to ``False`` if you intend to display or further
        modify the returned figures.

    :return: list of generated :class:`~matplotlib.figure.Figure` objects
    :rtype: List[Figure]
    """
    # Determine global depth range
    start_depth = min(
        swir_df["StartDepth"].min(),
        tir_df["StartDepth"].min(),
    )
    end_depth = max(
        swir_df["EndDepth"].max(),
        tir_df["EndDepth"].max(),
    )

    # Build default PDF metadata
    if pdf_metadata is None:
        pdf_metadata = {
            "Title": f"HyLogger\u2122 Spectral Summary Report for {boreholeid}",
            "Author": "National Virtual Core Library (NVCL)",
            "Subject": "HyLogger\u2122 Spectral Summary",
            "Keywords": "HyLogger, hyperspectral, report, NVCL, AuScope",
            "Creator": "nvcl_kit",
        }

    figures: List[Figure] = []
    pdf_context = (
        PdfPages(str(output_path), metadata=pdf_metadata)
        if output_path is not None
        else None
    )

    # Check if this is a single-page report (section depth >= total depth range)
    multi_page = section_depth < (end_depth - start_depth)

    try:
        # Optional full-hole overview page, only if the section depth is less than the total depth range
        if hole_overview and multi_page:
            overview_fig = create_summary_page(
                boreholeid,
                swir_df,
                tir_df,
                swir_cols,
                tir_cols,
                colours=colours,
                swir_scalar_set=swir_scalar_set,
                tir_scalar_set=tir_scalar_set,
                section_start=float(start_depth),
                section_end=float(end_depth),
                name=name,
                year_drilled=year_drilled,
                drill_type=drill_type,
                total_depth=total_depth,
                longitude=longitude,
                latitude=latitude,
                crs=crs,
                figsize=figsize,
                page_spec=page_spec,
                logo=logo,
            )

            figures.append(overview_fig)

            if pdf_context is not None:
                pdf_context.savefig(overview_fig, bbox_inches="tight")

            if close_figures:
                plt.close(overview_fig)

        for sec_start in range(int(start_depth), int(end_depth), int(section_depth)):
            # Stretch the figure if it's a single page otherwise maintain the scale throughout the report
            if multi_page:
                sec_end = sec_start + section_depth
            else:
                sec_end = min(sec_start + section_depth, end_depth)

            fig = create_summary_page(
                boreholeid,
                swir_df,
                tir_df,
                swir_cols,
                tir_cols,
                colours=colours,
                swir_scalar_set=swir_scalar_set,
                tir_scalar_set=tir_scalar_set,
                section_start=float(sec_start),
                section_end=float(sec_end),
                name=name,
                year_drilled=year_drilled,
                drill_type=drill_type,
                total_depth=total_depth,
                longitude=longitude,
                latitude=latitude,
                crs=crs,
                figsize=figsize,
                page_spec=page_spec,
                logo=logo,
            )

            figures.append(fig)

            if pdf_context is not None:
                pdf_context.savefig(fig, bbox_inches="tight")

            if close_figures:
                plt.close(fig)

    finally:
        if pdf_context is not None:
            pdf_context.close()

    LOGGER.debug(
        "Generated %d page(s) for borehole %s (%.0f–%.0f m)",
        len(figures),
        boreholeid,
        start_depth,
        end_depth,
    )

    return figures
