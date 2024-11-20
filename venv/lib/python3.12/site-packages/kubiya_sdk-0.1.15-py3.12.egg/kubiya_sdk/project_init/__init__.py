import os
import shutil
from pathlib import Path


class CLIProjectInitializer:
    def __init__(self):
        self.base_path = self._get_base_path()
        self.template_dir = self.base_path / "kubiya_cli/init_command_folder"
        self.destination_dir = Path.cwd()

    @staticmethod
    def _get_base_path() -> Path:
        return Path(__file__).resolve().parent.parent

    def initialize(self):
        self._validate_template_dir()
        self._copy_template_files()
        print("CLI project initialization complete!")

    def _validate_template_dir(self):
        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")

    def _copy_template_files(self):
        for root, dirs, files in os.walk(self.template_dir):
            rel_path = Path(root).relative_to(self.template_dir)
            target_dir = self.destination_dir / rel_path
            self._create_directory(target_dir)
            self._copy_files(root, target_dir, files)

    def _create_directory(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        # print(f"Created directory: {path}")

    def _copy_files(self, src_root: str, dst_dir: Path, files: list):
        for f in files:
            src_file = Path(src_root) / f
            dst_file = dst_dir / f
            shutil.copy2(src_file, dst_file)
            # print(f"Copied file: {dst_file}")
