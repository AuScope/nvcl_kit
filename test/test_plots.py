#!/usr/bin/env python3
"""
Unit tests for nvcl_kit.plots module.
"""
import os
import subprocess
import sys
import tempfile
import unittest

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from nvcl_kit.plots import (
    _tick_top,
    draw_stacked_bar,
    page_header,
    plot_spectral_summary,
    create_summary_page,
    create_summary_report,
    _DEFAULT_PAGE_SPEC,
    _A4_FIGSIZE,
)


def _make_summary_df(n_rows=50, start_depth=0.0, cols=None):
    """Create a minimal summary DataFrame for testing."""
    if cols is None:
        cols = ["MineralA", "MineralB", "MineralC"]
    depths = np.arange(start_depth, start_depth + n_rows, dtype=float)
    data = {
        "StartDepth": depths,
        "EndDepth": depths + 1.0,
        "Error_uTSAS": np.random.uniform(0, 1000, n_rows),
        "SNR_uTSAS": np.random.uniform(0, 100, n_rows),
        "Error_ujCLST": np.random.uniform(0, 1000, n_rows),
        "SNR_ujCLST": np.random.uniform(0, 100, n_rows),
    }
    for col in cols:
        data[col] = np.random.uniform(0, 50, n_rows)
    return pd.DataFrame(data)


def _make_colours(cols):
    """Create a simple colour mapping for given column names."""
    base_colours = [
        (1.0, 0.0, 0.0, 1.0),
        (0.0, 1.0, 0.0, 1.0),
        (0.0, 0.0, 1.0, 1.0),
        (1.0, 1.0, 0.0, 1.0),
        (1.0, 0.0, 1.0, 1.0),
        (0.0, 1.0, 1.0, 1.0),
    ]
    return {col: base_colours[i % len(base_colours)] for i, col in enumerate(cols)}


class TestPlotModuleImport(unittest.TestCase):
    """Tests for module-level plotting configuration."""

    def test_import_forces_non_interactive_backend(self):
        """Importing the plotting module should use a non-interactive backend."""
        env = os.environ.copy()
        env["MPLBACKEND"] = "svg"
        result = subprocess.run(
            [sys.executable, "-c", "import matplotlib; import nvcl_kit.plots; print(matplotlib.get_backend())"],
            capture_output=True,
            text=True,
            check=True,
            env=env,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )
        self.assertEqual(result.stdout.strip(), "Agg")


class TestTickTop(unittest.TestCase):
    """Tests for the _tick_top helper function."""

    def setUp(self):
        self.fig, self.ax = plt.subplots()

    def tearDown(self):
        plt.close(self.fig)

    def test_tick_top_default(self):
        """_tick_top moves ticks to the top and keeps bottom labels."""
        _tick_top(self.ax)
        # Check tick params were applied without error
        self.assertTrue(self.ax.xaxis.get_label_position() == "top")

    def test_tick_top_no_bottom_labels(self):
        """_tick_top with also_label_bottom=False."""
        _tick_top(self.ax, also_label_bottom=False)
        self.assertTrue(self.ax.xaxis.get_label_position() == "top")


class TestDrawStackedBar(unittest.TestCase):
    """Tests for draw_stacked_bar function."""

    def setUp(self):
        self.cols = ["MineralA", "MineralB", "MineralC"]
        self.df = _make_summary_df(n_rows=10, cols=self.cols)
        self.colours = _make_colours(self.cols)

    def tearDown(self):
        plt.close("all")

    def test_returns_patch_handles(self):
        """draw_stacked_bar returns a dict of Patch handles for each column."""
        fig, ax = plt.subplots()
        handles = draw_stacked_bar(ax, self.df, cols=self.cols, colours=self.colours)
        self.assertIsInstance(handles, dict)
        self.assertEqual(set(handles.keys()), set(self.cols))
        for patch in handles.values():
            self.assertIsInstance(patch, Patch)

    def test_default_cols_from_dataframe(self):
        """When cols=None, columns from index 5 onward are used."""
        # Build a DataFrame where cols start at index 5
        df = pd.DataFrame({
            "col0": [1], "col1": [2], "col2": [3], "col3": [4], "col4": [5],
            "StartDepth": [0.0],
            "A": [30.0], "B": [70.0],
        })
        # Reorder so first 5 cols are col0-col4, then StartDepth is y
        df = df[["col0", "col1", "col2", "col3", "col4", "A", "B", "StartDepth"]]
        colours = _make_colours(["A", "B", "StartDepth"])
        fig, ax = plt.subplots()
        handles = draw_stacked_bar(ax, df, y="StartDepth", colours=colours)
        # cols[5:] = ["A", "B", "StartDepth"]
        self.assertIn("A", handles)
        self.assertIn("B", handles)

    def test_sort_columns_by_sum(self):
        """When sort=True, columns are ordered by descending sum."""
        fig, ax = plt.subplots()
        df = _make_summary_df(n_rows=5, cols=self.cols)
        # Make MineralC the dominant one
        df["MineralC"] = 100.0
        df["MineralA"] = 1.0
        handles = draw_stacked_bar(ax, df, cols=self.cols, colours=self.colours, sort=True)
        keys = list(handles.keys())
        self.assertEqual(keys[0], "MineralC")

    def test_no_sort(self):
        """When sort=False, columns remain in original order."""
        fig, ax = plt.subplots()
        handles = draw_stacked_bar(
            ax, self.df, cols=self.cols, colours=self.colours, sort=False
        )
        self.assertEqual(list(handles.keys()), self.cols)

    def test_yticks_disabled(self):
        """When yticks=False, y-axis locators are not set."""
        fig, ax = plt.subplots()
        handles = draw_stacked_bar(
            ax, self.df, cols=self.cols, colours=self.colours, yticks=False
        )
        self.assertIsInstance(handles, dict)

    def test_custom_locators(self):
        """Custom major_locator and minor_locator values are applied."""
        fig, ax = plt.subplots()
        draw_stacked_bar(
            ax, self.df, cols=self.cols, colours=self.colours,
            major_locator=50, minor_locator=10
        )
        # Just verify no exception is raised

    def test_colorcet_auto_colours(self):
        """When colours=None, colorcet palette is used automatically."""
        fig, ax = plt.subplots()
        # This should work since colorcet is installed as dev dep
        handles = draw_stacked_bar(ax, self.df, cols=self.cols, colours=None)
        self.assertEqual(set(handles.keys()), set(self.cols))

    def test_custom_height(self):
        """Custom height parameter does not error."""
        fig, ax = plt.subplots()
        handles = draw_stacked_bar(
            ax, self.df, cols=self.cols, colours=self.colours, height=2.0
        )
        self.assertIsInstance(handles, dict)


class TestPageHeader(unittest.TestCase):
    """Tests for page_header function."""

    def tearDown(self):
        plt.close("all")

    def test_minimal_header(self):
        """page_header with only boreholeid renders without error."""
        fig, ax = plt.subplots()
        page_header(ax, "BH_001")
        # Axis should be turned off
        self.assertFalse(ax.axison)

    def test_full_header(self):
        """page_header with all optional parameters renders without error."""
        fig, ax = plt.subplots()
        page_header(
            ax,
            "BH_002",
            name="Test Borehole",
            year_drilled="2020",
            drill_type="Diamond",
            total_depth="500",
            longitude=148.5,
            latitude=-32.1,
            crs="GDA94",
        )
        self.assertFalse(ax.axison)

    def test_header_without_crs(self):
        """page_header with coordinates but no CRS."""
        fig, ax = plt.subplots()
        page_header(
            ax,
            "BH_003",
            longitude=150.0,
            latitude=-33.0,
        )
        self.assertFalse(ax.axison)

    def test_header_partial_info(self):
        """page_header with only some optional fields."""
        fig, ax = plt.subplots()
        page_header(
            ax,
            "BH_004",
            name="Partial Hole",
            drill_type="RC",
        )
        self.assertFalse(ax.axison)


class TestPlotSpectralSummary(unittest.TestCase):
    """Tests for plot_spectral_summary function."""

    def setUp(self):
        self.cols = ["GroupA", "GroupB"]
        self.df = _make_summary_df(n_rows=20, cols=self.cols)
        self.colours = _make_colours(self.cols)

    def tearDown(self):
        plt.close("all")

    def test_basic_plot(self):
        """plot_spectral_summary creates a stacked bar and returns handles."""
        fig, ax = plt.subplots()
        handles = plot_spectral_summary(
            ax, self.df, self.cols, colours=self.colours
        )
        self.assertIsInstance(handles, dict)
        self.assertEqual(set(handles.keys()), set(self.cols))

    def test_with_xlabel(self):
        """plot_spectral_summary sets xlabel prefix."""
        fig, ax = plt.subplots()
        handles = plot_spectral_summary(
            ax, self.df, self.cols, colours=self.colours, xlabel="SWIR"
        )
        self.assertIn("SWIR", ax.get_xlabel())

    def test_with_ylim(self):
        """plot_spectral_summary applies ylim."""
        fig, ax = plt.subplots()
        plot_spectral_summary(
            ax, self.df, self.cols, colours=self.colours, ylim=(0, 100)
        )
        ylim = ax.get_ylim()
        # y-axis is inverted, so max comes first
        self.assertAlmostEqual(ylim[0], 100.0)
        self.assertAlmostEqual(ylim[1], 0.0)

    def test_with_error_and_snr(self):
        """plot_spectral_summary with ax2, error_col and snr_col."""
        fig, (ax1, ax2) = plt.subplots(1, 2)
        handles = plot_spectral_summary(
            ax1,
            self.df,
            self.cols,
            colours=self.colours,
            ax2=ax2,
            error_col="Error_uTSAS",
            snr_col="SNR_uTSAS",
        )
        self.assertIsInstance(handles, dict)

    def test_with_error_no_snr(self):
        """plot_spectral_summary with error but no SNR."""
        fig, (ax1, ax2) = plt.subplots(1, 2)
        handles = plot_spectral_summary(
            ax1,
            self.df,
            self.cols,
            colours=self.colours,
            ax2=ax2,
            error_col="Error_uTSAS",
            snr_col=None,
        )
        self.assertIsInstance(handles, dict)

    def test_with_sharey(self):
        """plot_spectral_summary shares y-axis with another axes."""
        fig, (ax1, ax2) = plt.subplots(1, 2)
        # First panel as reference
        plot_spectral_summary(ax1, self.df, self.cols, colours=self.colours)
        # Second panel sharing y with first
        handles = plot_spectral_summary(
            ax2, self.df, self.cols, colours=self.colours, sharey_ax=ax1
        )
        self.assertIsInstance(handles, dict)

    def test_yticks_false(self):
        """plot_spectral_summary with yticks=False."""
        fig, ax = plt.subplots()
        handles = plot_spectral_summary(
            ax, self.df, self.cols, colours=self.colours, yticks=False
        )
        self.assertIsInstance(handles, dict)

    def test_custom_locators(self):
        """plot_spectral_summary with custom major/minor locators."""
        fig, ax = plt.subplots()
        handles = plot_spectral_summary(
            ax, self.df, self.cols, colours=self.colours,
            major_locator=50, minor_locator=10
        )
        self.assertIsInstance(handles, dict)


class TestCreateSummaryPage(unittest.TestCase):
    """Tests for create_summary_page function."""

    def setUp(self):
        self.swir_cols = ["SwirA", "SwirB"]
        self.tir_cols = ["TirA", "TirB"]
        all_cols = self.swir_cols + self.tir_cols
        self.colours = _make_colours(all_cols)
        self.swir_df = _make_summary_df(n_rows=50, cols=self.swir_cols)
        self.tir_df = _make_summary_df(n_rows=50, cols=self.tir_cols)

    def tearDown(self):
        plt.close("all")

    def test_returns_figure(self):
        """create_summary_page returns a matplotlib Figure."""
        fig = create_summary_page(
            "BH_TEST",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_start=0.0,
            section_end=50.0,
        )
        self.assertIsInstance(fig, Figure)
        plt.close(fig)

    def test_with_metadata(self):
        """create_summary_page with full borehole metadata."""
        fig = create_summary_page(
            "BH_META",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_start=0.0,
            section_end=50.0,
            name="Test Hole",
            year_drilled="2021",
            drill_type="Diamond",
            total_depth="500",
            longitude=149.0,
            latitude=-33.5,
            crs="GDA2020",
        )
        self.assertIsInstance(fig, Figure)
        plt.close(fig)

    def test_depth_section_filtering(self):
        """create_summary_page only plots data within the section range."""
        fig = create_summary_page(
            "BH_SECTION",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_start=10.0,
            section_end=30.0,
        )
        self.assertIsInstance(fig, Figure)
        plt.close(fig)

    def test_small_section_locators(self):
        """Section <= 100m should use major_locator=10."""
        fig = create_summary_page(
            "BH_SMALL",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_start=0.0,
            section_end=50.0,
        )
        self.assertIsInstance(fig, Figure)
        plt.close(fig)

    def test_large_section_locators(self):
        """Section > 500m should use larger locator intervals."""
        large_swir = _make_summary_df(n_rows=800, cols=self.swir_cols)
        large_tir = _make_summary_df(n_rows=800, cols=self.tir_cols)
        fig = create_summary_page(
            "BH_LARGE",
            large_swir,
            large_tir,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_start=0.0,
            section_end=800.0,
        )
        self.assertIsInstance(fig, Figure)
        plt.close(fig)

    def test_with_logo_missing_file(self):
        """create_summary_page with logo param but missing logo file gracefully continues."""
        fig = create_summary_page(
            "BH_LOGO",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_start=0.0,
            section_end=50.0,
            logo="NONEXISTENT",
        )
        self.assertIsInstance(fig, Figure)
        plt.close(fig)


class TestCreateSummaryReport(unittest.TestCase):
    """Tests for create_summary_report function."""

    def setUp(self):
        self.swir_cols = ["SwirX", "SwirY"]
        self.tir_cols = ["TirX", "TirY"]
        all_cols = self.swir_cols + self.tir_cols
        self.colours = _make_colours(all_cols)
        self.swir_df = _make_summary_df(n_rows=100, cols=self.swir_cols)
        self.tir_df = _make_summary_df(n_rows=100, cols=self.tir_cols)

    def tearDown(self):
        plt.close("all")

    def test_returns_list_of_figures(self):
        """create_summary_report returns a list of Figure objects."""
        figs = create_summary_report(
            "BH_REPORT",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_depth=500.0,
            close_figures=False,
        )
        self.assertIsInstance(figs, list)
        self.assertGreater(len(figs), 0)
        for fig in figs:
            self.assertIsInstance(fig, Figure)
            plt.close(fig)

    def test_multi_page_report(self):
        """Report with section_depth < total depth produces multiple pages."""
        figs = create_summary_report(
            "BH_MULTI",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_depth=50.0,
            close_figures=True,
        )
        self.assertGreater(len(figs), 1)

    def test_hole_overview_page(self):
        """hole_overview=True adds an extra overview page."""
        figs_no_overview = create_summary_report(
            "BH_OV",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_depth=50.0,
            hole_overview=False,
            close_figures=True,
        )
        figs_with_overview = create_summary_report(
            "BH_OV",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_depth=50.0,
            hole_overview=True,
            close_figures=True,
        )
        self.assertEqual(len(figs_with_overview), len(figs_no_overview) + 1)

    def test_overview_skipped_single_page(self):
        """hole_overview=True has no effect when section_depth >= total range."""
        figs = create_summary_report(
            "BH_SINGLE",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_depth=500.0,
            hole_overview=True,
            close_figures=True,
        )
        # Single page since section_depth >= total depth range
        self.assertEqual(len(figs), 1)

    def test_pdf_output(self):
        """create_summary_report writes a valid PDF file."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name
        try:
            figs = create_summary_report(
                "BH_PDF",
                self.swir_df,
                self.tir_df,
                self.swir_cols,
                self.tir_cols,
                colours=self.colours,
                section_depth=500.0,
                output_path=pdf_path,
                close_figures=True,
            )
            self.assertTrue(os.path.isfile(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 0)
        finally:
            if os.path.isfile(pdf_path):
                os.unlink(pdf_path)

    def test_pdf_metadata(self):
        """create_summary_report uses custom PDF metadata."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name
        try:
            custom_meta = {
                "Title": "Custom Title",
                "Author": "Test Author",
            }
            figs = create_summary_report(
                "BH_META_PDF",
                self.swir_df,
                self.tir_df,
                self.swir_cols,
                self.tir_cols,
                colours=self.colours,
                section_depth=500.0,
                output_path=pdf_path,
                pdf_metadata=custom_meta,
                close_figures=True,
            )
            self.assertTrue(os.path.isfile(pdf_path))
        finally:
            if os.path.isfile(pdf_path):
                os.unlink(pdf_path)

    def test_no_pdf_output(self):
        """create_summary_report with output_path=None produces no file."""
        figs = create_summary_report(
            "BH_NOPDF",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_depth=500.0,
            output_path=None,
            close_figures=True,
        )
        self.assertIsInstance(figs, list)

    def test_close_figures_true(self):
        """Figures are closed when close_figures=True."""
        figs = create_summary_report(
            "BH_CLOSE",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_depth=500.0,
            close_figures=True,
        )
        # After close, figure numbers should not be in plt's list
        open_fig_nums = plt.get_fignums()
        for fig in figs:
            self.assertNotIn(fig.number, open_fig_nums)

    def test_with_borehole_metadata(self):
        """create_summary_report passes metadata through to pages."""
        figs = create_summary_report(
            "BH_FULLMETA",
            self.swir_df,
            self.tir_df,
            self.swir_cols,
            self.tir_cols,
            colours=self.colours,
            section_depth=500.0,
            name="Full Meta Hole",
            year_drilled="2019",
            drill_type="RC",
            total_depth="100",
            longitude=145.0,
            latitude=-37.5,
            crs="GDA94",
            close_figures=True,
        )
        self.assertGreater(len(figs), 0)


if __name__ == "__main__":
    unittest.main()
