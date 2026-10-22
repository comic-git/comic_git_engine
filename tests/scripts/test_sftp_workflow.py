"""Check reusable-workflow wiring; deployment behavior is tested as Python."""
from pathlib import Path
import re
from unittest import TestCase

WORKFLOW = Path(__file__).resolve().parents[2] / '.github/workflows/build_site.yaml'


class TestSftpWorkflow(TestCase):
    def test_workflow_routes_sftp_and_preserves_existing_defaults(self):
        workflow = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('default: github-pages', workflow)
        self.assertNotIn('Stage SFTP artifact', workflow)
        self.assertIn('build_args+=(--hidden-paths "$SFTP_HIDDEN_PATHS")', workflow)
        self.assertIn('if [[ "$DEPLOY_TARGET" == "sftp" ]]', workflow)
        self.assertIn("include-hidden-files: ${{ inputs.DEPLOY_TARGET == 'sftp' }}", workflow)
        self.assertIn("if: ${{ inputs.DEPLOY_TARGET == 'sftp' }}", workflow)
        download_paths = re.findall(r'uses: actions/download-artifact@[0-9a-f]{40}[^\n]*\s+with:\s+name: site\s+path: (.+)', workflow)
        self.assertEqual(["${{ inputs.OUTPUT_DIR || '.' }}"] * 3, download_paths)
        deploy_job = workflow.split('  deploy-sftp:', 1)[1]
        self.assertNotIn('shell: python', deploy_job)
        self.assertNotIn('SFTP_REMOTE_DIR:', deploy_job)
        self.assertIn('name: sftp-deployment', deploy_job)
        self.assertIn('run: python "$RUNNER_TEMP/sftp-deployment/deploy.py" --output-dir "$OUTPUT_DIR"', deploy_job)
