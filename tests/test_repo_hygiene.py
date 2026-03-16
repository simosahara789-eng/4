import subprocess
import unittest


class RepoHygieneTests(unittest.TestCase):
    def test_no_merge_conflict_markers_in_tracked_files(self):
        result = subprocess.run(
            ["git", "grep", "-nE", "^(<<<<<<<|=======|>>>>>>>)"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            1,
            msg=(
                "Found merge conflict markers in tracked files:\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            ),
        )


if __name__ == "__main__":
    unittest.main()
