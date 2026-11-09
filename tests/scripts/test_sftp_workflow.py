"""Check reusable-workflow wiring; deployment behavior is tested as Python."""
from pathlib import Path
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
        build_job, deploy_job = workflow.split("  deploy-sftp:", 1)
        self.assertIn("engine_sha: ${{ steps.engine-checkout.outputs.commit }}", build_job)
        self.assertNotIn("SFTP_PASSWORD:", build_job.split("jobs:", 1)[1])
        self.assertNotIn("SFTP_PRIVATE_KEY:", build_job.split("jobs:", 1)[1])
        self.assertNotIn("SFTP_REMOTE_DIR:", build_job.split("jobs:", 1)[1])
        self.assertIn("ref: ${{ needs.build.outputs.engine_sha }}", deploy_job)
        self.assertIn("path: ${{ runner.temp }}/comic-git-site", deploy_job)
        self.assertIn("SITE_DIR: ${{ runner.temp }}/comic-git-site", deploy_job)
        self.assertIn("requirements_sftp.txt", deploy_job)
        self.assertIn('deploy_sftp.py --upload-only "$SITE_DIR"', deploy_job)
        self.assertNotIn("sftp-deployment", workflow)
        self.assertNotIn("lftp", workflow)
