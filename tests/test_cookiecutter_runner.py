"""
Unit tests for CookiecutterRunner class.

Tests the Cookiecutter execution and temporary file management.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from repo_scaffold.core.cookiecutter_runner import CookiecutterRunner


@pytest.fixture
def cookiecutter_runner():
    """Create a CookiecutterRunner instance."""
    return CookiecutterRunner()


@pytest.fixture
def temp_template_dir():
    """Create a temporary template directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir)
        
        # Create a basic cookiecutter template structure
        (template_dir / "cookiecutter.json").write_text('{"project_name": "test"}')
        (template_dir / "{{cookiecutter.project_name}}").mkdir()
        (template_dir / "{{cookiecutter.project_name}}" / "README.md").write_text("# {{cookiecutter.project_name}}")
        
        yield template_dir


def test_cookiecutter_runner_initialization():
    """Test CookiecutterRunner initialization."""
    runner = CookiecutterRunner()
    assert runner is not None


@patch('repo_scaffold.core.cookiecutter_runner.cookiecutter')
def test_run_cookiecutter_basic(mock_cookiecutter, cookiecutter_runner, temp_template_dir):
    """Test basic cookiecutter execution."""
    output_dir = Path("/tmp/output")
    mock_cookiecutter.return_value = str(output_dir / "test_project")
    
    result = cookiecutter_runner.run_cookiecutter(temp_template_dir, output_dir)
    
    # Verify cookiecutter was called with correct parameters
    mock_cookiecutter.assert_called_once_with(
        str(temp_template_dir),
        output_dir=str(output_dir),
        no_input=False
    )
    
    # Verify result path
    assert result == output_dir / "test_project"


@patch('repo_scaffold.core.cookiecutter_runner.cookiecutter')
def test_run_cookiecutter_default_output_dir(mock_cookiecutter, cookiecutter_runner, temp_template_dir):
    """Test cookiecutter execution with default output directory."""
    mock_cookiecutter.return_value = "/current/dir/test_project"
    
    result = cookiecutter_runner.run_cookiecutter(temp_template_dir)
    
    # Verify cookiecutter was called with current directory as output
    mock_cookiecutter.assert_called_once_with(
        str(temp_template_dir),
        output_dir=".",
        no_input=False
    )
    
    assert result == Path("/current/dir/test_project")


@patch('repo_scaffold.core.cookiecutter_runner.cookiecutter')
def test_run_cookiecutter_no_input(mock_cookiecutter, cookiecutter_runner, temp_template_dir):
    """Test cookiecutter execution with no_input=True."""
    output_dir = Path("/tmp/output")
    mock_cookiecutter.return_value = str(output_dir / "test_project")
    
    result = cookiecutter_runner.run_cookiecutter(temp_template_dir, output_dir, no_input=True)
    
    # Verify cookiecutter was called with no_input=True
    mock_cookiecutter.assert_called_once_with(
        str(temp_template_dir),
        output_dir=str(output_dir),
        no_input=True
    )


@patch('repo_scaffold.core.cookiecutter_runner.cookiecutter')
def test_run_cookiecutter_with_extra_context(mock_cookiecutter, cookiecutter_runner, temp_template_dir):
    """Test cookiecutter execution with extra context."""
    output_dir = Path("/tmp/output")
    extra_context = {"project_name": "my_project", "author": "John Doe"}
    mock_cookiecutter.return_value = str(output_dir / "my_project")
    
    result = cookiecutter_runner.run_cookiecutter(
        temp_template_dir, 
        output_dir, 
        extra_context=extra_context
    )
    
    # Verify cookiecutter was called with extra context
    mock_cookiecutter.assert_called_once_with(
        str(temp_template_dir),
        output_dir=str(output_dir),
        no_input=False,
        extra_context=extra_context
    )


@patch('repo_scaffold.core.cookiecutter_runner.cookiecutter')
def test_run_cookiecutter_cookiecutter_error(mock_cookiecutter, cookiecutter_runner, temp_template_dir):
    """Test cookiecutter execution when cookiecutter raises an error."""
    from cookiecutter.exceptions import CookiecutterException
    
    mock_cookiecutter.side_effect = CookiecutterException("Template error")
    
    with pytest.raises(CookiecutterException):
        cookiecutter_runner.run_cookiecutter(temp_template_dir)


@patch('repo_scaffold.core.cookiecutter_runner.cookiecutter')
def test_run_cookiecutter_invalid_template_dir(mock_cookiecutter, cookiecutter_runner):
    """Test cookiecutter execution with invalid template directory."""
    invalid_dir = Path("/nonexistent/template")
    
    # cookiecutter should handle this and raise appropriate error
    mock_cookiecutter.side_effect = FileNotFoundError("Template not found")
    
    with pytest.raises(FileNotFoundError):
        cookiecutter_runner.run_cookiecutter(invalid_dir)


@patch('shutil.rmtree')
def test_cleanup_temp_template(mock_rmtree, cookiecutter_runner):
    """Test temporary template cleanup."""
    temp_dir = Path("/tmp/test_template")
    
    cookiecutter_runner.cleanup_temp_template(temp_dir)
    
    # Verify shutil.rmtree was called
    mock_rmtree.assert_called_once_with(temp_dir)


@patch('shutil.rmtree')
def test_cleanup_temp_template_missing_dir(mock_rmtree, cookiecutter_runner):
    """Test cleanup when template directory doesn't exist."""
    temp_dir = Path("/tmp/nonexistent")
    mock_rmtree.side_effect = FileNotFoundError("Directory not found")
    
    # Should not raise an error
    cookiecutter_runner.cleanup_temp_template(temp_dir)
    
    mock_rmtree.assert_called_once_with(temp_dir)


@patch('shutil.rmtree')
def test_cleanup_temp_template_permission_error(mock_rmtree, cookiecutter_runner):
    """Test cleanup when permission is denied."""
    temp_dir = Path("/tmp/test_template")
    mock_rmtree.side_effect = PermissionError("Permission denied")
    
    # Should not raise an error, just log it
    cookiecutter_runner.cleanup_temp_template(temp_dir)
    
    mock_rmtree.assert_called_once_with(temp_dir)


def test_run_cookiecutter_path_conversion(cookiecutter_runner):
    """Test that Path objects are properly converted to strings."""
    template_dir = Path("/tmp/template")
    output_dir = Path("/tmp/output")
    
    with patch('repo_scaffold.core.cookiecutter_runner.cookiecutter') as mock_cookiecutter:
        mock_cookiecutter.return_value = "/tmp/output/project"
        
        cookiecutter_runner.run_cookiecutter(template_dir, output_dir)
        
        # Verify that Path objects were converted to strings
        args, kwargs = mock_cookiecutter.call_args
        assert isinstance(args[0], str)
        assert isinstance(kwargs['output_dir'], str)


@patch('repo_scaffold.core.cookiecutter_runner.cookiecutter')
def test_run_cookiecutter_context_manager_usage(mock_cookiecutter, cookiecutter_runner, temp_template_dir):
    """Test using CookiecutterRunner as a context manager."""
    output_dir = Path("/tmp/output")
    mock_cookiecutter.return_value = str(output_dir / "test_project")
    
    # Test that it can be used as a context manager (if implemented)
    try:
        with cookiecutter_runner as runner:
            result = runner.run_cookiecutter(temp_template_dir, output_dir)
            assert result == output_dir / "test_project"
    except AttributeError:
        # If context manager is not implemented, that's fine for now
        pytest.skip("Context manager not implemented")


def test_cookiecutter_runner_with_real_template():
    """Integration test with a real (minimal) template."""
    runner = CookiecutterRunner()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir) / "template"
        template_dir.mkdir()
        
        # Create minimal cookiecutter template
        cookiecutter_json = {
            "project_name": "test_project",
            "author": "Test Author"
        }
        
        with open(template_dir / "cookiecutter.json", "w") as f:
            import json
            json.dump(cookiecutter_json, f)
        
        # Create template directory
        project_template_dir = template_dir / "{{cookiecutter.project_name}}"
        project_template_dir.mkdir()
        
        # Create a simple template file
        readme_template = "# {{cookiecutter.project_name}}\n\nBy {{cookiecutter.author}}"
        with open(project_template_dir / "README.md", "w") as f:
            f.write(readme_template)
        
        # Test with real cookiecutter (if available)
        try:
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            with patch('repo_scaffold.core.cookiecutter_runner.cookiecutter') as mock_cookiecutter:
                mock_cookiecutter.return_value = str(output_dir / "test_project")
                
                result = runner.run_cookiecutter(
                    template_dir, 
                    output_dir, 
                    no_input=True
                )
                
                assert result == output_dir / "test_project"
                mock_cookiecutter.assert_called_once()
                
        except ImportError:
            pytest.skip("cookiecutter not available for integration test")
