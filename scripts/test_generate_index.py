#!/usr/bin/env python3
"""
Test suite for generate-index.py multi-page generation.

Tests the multi-page functionality that splits distributions into separate pages.
"""

import pytest
import sys
from pathlib import Path
from generate_index import (
    Package,
    Distribution,
    render_distribution_summary_card,
    render_main_index,
    render_distribution_page,
    render_component_group,
    scan_distributions,
    get_distribution_info,
    get_component_display_name,
)


@pytest.fixture
def sample_distribution():
    """Create a sample distribution with test data."""
    packages = [
        Package(
            name='test-pkg-1',
            version='1.0.0',
            description='First test package',
            architecture='arm64',
            filename='pool/test-pkg-1_1.0.0_arm64.deb',
            component='main',
            all_architectures=['arm64']
        ),
        Package(
            name='test-pkg-2',
            version='2.1.0',
            description='Second test package',
            architecture='all',
            filename='pool/test-pkg-2_2.1.0_all.deb',
            component='main',
            all_architectures=['all']
        ),
    ]

    return Distribution(
        name='trixie-stable',
        display_name='Trixie Stable',
        description='HaLOS packages for Debian Trixie (stable releases)',
        packages=packages
    )


@pytest.fixture
def empty_distribution():
    """Create a distribution with no packages."""
    return Distribution(
        name='bookworm-unstable',
        display_name='Bookworm Unstable',
        description='HaLOS packages for Debian Bookworm (rolling)',
        packages=[]
    )


@pytest.fixture
def all_distributions():
    """Create all 4 test distributions."""
    return [
        Distribution(
            name='bookworm-stable',
            display_name='Bookworm Stable',
            description='HaLOS packages for Debian Bookworm (stable releases)',
            packages=[]
        ),
        Distribution(
            name='bookworm-unstable',
            display_name='Bookworm Unstable',
            description='HaLOS packages for Debian Bookworm (rolling)',
            packages=[]
        ),
        Distribution(
            name='trixie-stable',
            display_name='Trixie Stable',
            description='HaLOS packages for Debian Trixie (stable releases)',
            packages=[
                Package(
                    name='pkg-a',
                    version='1.0',
                    description='Package A',
                    architecture='all',
                    filename='pool/pkg-a_1.0_all.deb',
                    component='main',
                    all_architectures=['all']
                )
            ]
        ),
        Distribution(
            name='trixie-unstable',
            display_name='Trixie Unstable',
            description='HaLOS packages for Debian Trixie (rolling)',
            packages=[]
        ),
    ]


class TestDistributionSummaryCard:
    """Tests for distribution summary card rendering (for main index)."""

    def test_summary_card_contains_distribution_name(self, sample_distribution):
        html = render_distribution_summary_card(sample_distribution)
        assert 'Trixie Stable' in html

    def test_summary_card_contains_package_count(self, sample_distribution):
        html = render_distribution_summary_card(sample_distribution)
        assert '2 packages' in html

    def test_summary_card_contains_description(self, sample_distribution):
        html = render_distribution_summary_card(sample_distribution)
        assert 'HaLOS packages for Debian Trixie' in html

    def test_summary_card_no_package_list(self, sample_distribution):
        html = render_distribution_summary_card(sample_distribution)
        assert 'test-pkg-1' not in html
        assert 'test-pkg-2' not in html
        assert 'package-list' not in html

    def test_summary_card_contains_link_to_distribution_page(self, sample_distribution):
        html = render_distribution_summary_card(sample_distribution)
        assert 'trixie-stable.html' in html

    def test_summary_card_zero_packages(self, empty_distribution):
        html = render_distribution_summary_card(empty_distribution)
        assert '0 packages' in html
        assert 'Bookworm Unstable' in html


class TestDistributionPage:
    """Tests for individual distribution page rendering."""

    def test_distribution_page_title(self, sample_distribution):
        html = render_distribution_page(sample_distribution, 'ABC123')
        assert 'Trixie Stable' in html

    def test_distribution_page_contains_packages(self, sample_distribution):
        html = render_distribution_page(sample_distribution, 'ABC123')
        assert 'test-pkg-1' in html
        assert 'test-pkg-2' in html

    def test_distribution_page_package_versions(self, sample_distribution):
        html = render_distribution_page(sample_distribution, 'ABC123')
        assert '1.0.0' in html
        assert '2.1.0' in html

    def test_distribution_page_has_breadcrumb(self, sample_distribution):
        html = render_distribution_page(sample_distribution, 'ABC123')
        assert 'index.html' in html

    def test_distribution_page_unstable_warning(self):
        dist = Distribution(
            name='trixie-unstable',
            display_name='Trixie Unstable',
            description='Test unstable',
            packages=[]
        )
        html = render_distribution_page(dist, 'ABC123')
        assert 'Unstable Channel' in html

    def test_distribution_page_no_unstable_warning_for_stable(self, sample_distribution):
        html = render_distribution_page(sample_distribution, 'ABC123')
        assert 'Unstable Channel' not in html

    def test_distribution_page_empty_packages(self, empty_distribution):
        html = render_distribution_page(empty_distribution, 'ABC123')
        assert 'Bookworm Unstable' in html
        assert 'No packages' in html

    def test_distribution_page_setup_command(self, sample_distribution):
        html = render_distribution_page(sample_distribution, 'ABC123')
        assert 'trixie-stable' in html

    def test_distribution_page_gpg_fingerprint(self, sample_distribution):
        html = render_distribution_page(sample_distribution, 'ABC123DEF456')
        assert 'ABC123DEF456' in html

    def test_distribution_page_uses_halos_urls(self, sample_distribution):
        html = render_distribution_page(sample_distribution, 'ABC123')
        assert 'apt.halos.fi' in html
        assert 'halos-apt-key.asc' in html


class TestMainIndex:
    """Tests for main index page rendering."""

    def test_main_index_has_setup_instructions(self, all_distributions):
        html = render_main_index(all_distributions, 'ABC123')
        assert 'Repository Setup' in html

    def test_main_index_has_all_distribution_cards(self, all_distributions):
        html = render_main_index(all_distributions, 'ABC123')
        assert 'Bookworm Stable' in html
        assert 'Bookworm Unstable' in html
        assert 'Trixie Stable' in html
        assert 'Trixie Unstable' in html

    def test_main_index_no_individual_packages(self, all_distributions):
        html = render_main_index(all_distributions, 'ABC123')
        assert 'pkg-a' not in html

    def test_main_index_links_to_distribution_pages(self, all_distributions):
        html = render_main_index(all_distributions, 'ABC123')
        assert 'bookworm-stable.html' in html
        assert 'bookworm-unstable.html' in html
        assert 'trixie-stable.html' in html
        assert 'trixie-unstable.html' in html

    def test_main_index_gpg_fingerprint(self, all_distributions):
        html = render_main_index(all_distributions, 'TEST12345')
        assert 'TEST12345' in html

    def test_main_index_responsive_design(self, all_distributions):
        html = render_main_index(all_distributions, 'ABC123')
        assert '<link rel="stylesheet" href="styles.css">' in html
        assert 'viewport' in html

    def test_main_index_uses_halos_urls(self, all_distributions):
        html = render_main_index(all_distributions, 'ABC123')
        assert 'apt.halos.fi' in html
        assert 'halos-apt-key.asc' in html
        assert 'halos.list' in html


class TestMultiPageGeneration:
    """Integration tests for complete multi-page generation."""

    def test_functions_exist(self):
        assert callable(render_distribution_summary_card)
        assert callable(render_main_index)
        assert callable(render_distribution_page)

    def test_main_index_is_html(self, all_distributions):
        html = render_main_index(all_distributions, 'ABC123')
        assert '<!DOCTYPE html>' in html
        assert '<html' in html
        assert '</html>' in html

    def test_distribution_page_is_html(self, sample_distribution):
        html = render_distribution_page(sample_distribution, 'ABC123')
        assert '<!DOCTYPE html>' in html
        assert '<html' in html
        assert '</html>' in html


class TestFullWorkflowIntegration:
    """Integration tests for complete workflow with main() function."""

    def test_main_generates_all_files(self, tmp_path):
        repo_dir = tmp_path / "apt-repo"
        dists_dir = repo_dir / "dists"
        dists_dir.mkdir(parents=True)

        for dist in ['bookworm-stable', 'bookworm-unstable', 'trixie-stable', 'trixie-unstable']:
            dist_path = dists_dir / dist / 'main' / 'binary-all'
            dist_path.mkdir(parents=True)
            (dist_path / 'Packages').touch()

        original_argv = sys.argv
        try:
            sys.argv = [
                'generate_index.py',
                str(repo_dir),
                '--gpg-fingerprint', 'TEST_FINGERPRINT_123'
            ]

            import generate_index
            result = generate_index.main()

            assert result == 0, "main() should return 0 on success"

            assert (repo_dir / 'index.html').exists(), "index.html should exist"
            assert (repo_dir / 'styles.css').exists(), "styles.css should exist"

            for dist in ['bookworm-stable', 'bookworm-unstable', 'trixie-stable', 'trixie-unstable']:
                html_file = repo_dir / f'{dist}.html'
                assert html_file.exists(), f"{dist}.html should exist"

                html_content = html_file.read_text()
                assert 'styles.css' in html_content, f"{dist}.html should link to styles.css"

        finally:
            sys.argv = original_argv

    def test_css_file_has_required_styles(self, tmp_path):
        import generate_index

        repo_dir = tmp_path / "apt-repo"
        dists_dir = repo_dir / "dists"
        dists_dir.mkdir(parents=True)

        original_argv = sys.argv
        try:
            sys.argv = [
                'generate_index.py',
                str(repo_dir),
                '--gpg-fingerprint', 'TEST'
            ]

            generate_index.main()

            css_file = repo_dir / 'styles.css'
            css_content = css_file.read_text()

            assert '.dist-card' in css_content
            assert '.breadcrumb' in css_content
            assert '.package-item' in css_content
            assert '@media' in css_content

        finally:
            sys.argv = original_argv


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
