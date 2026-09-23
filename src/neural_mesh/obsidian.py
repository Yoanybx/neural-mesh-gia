from pathlib import Path
from .models import Checkpoint
class ObsidianSync:
    def __init__(self, root):
        self.vault=Path(root)/"obsidian"/"Neural-Mesh-Vault"
    def bootstrap(self):
        dirs=["01_ARCHITECTURE","02_COMPONENTS","03_PROTOCOLS","04_MEMORY",
              "05_ROUTING","06_VERIFICATION","07_FAULT_TOLERANCE","08_EXPERIMENTS",
              "09_BENCHMARKS","10_DECISIONS","11_CHECKPOINTS","12_SESSIONS",
              "13_BUGS","14_ROADMAP","99_ARCHIVE"]
        self.vault.mkdir(parents=True,exist_ok=True)
        for d in dirs:(self.vault/d).mkdir(exist_ok=True)
        (self.vault/"00_INDEX.md").write_text(
            "# NEURAL MESH / GIA-COS\n\n"
            "## State\n[[CURRENT_STATE]]\n[[NEXT_ACTION]]\n[[Latest Checkpoint]]\n\n"
            "## Architecture\n[[GIA-COS]] [[C-RAM]] [[World Model]] [[Cognitive Router]] "
            "[[Verification Mesh]] [[Fault Tolerance]]\n",encoding="utf-8")
    def record_checkpoint(self,cp:Checkpoint):
        self.bootstrap()
        p=self.vault/"11_CHECKPOINTS"/f"{cp.checkpoint_id}.md"
        p.write_text(f"# {cp.checkpoint_id}\n\nPhase: {cp.phase}\nModule: {cp.module}\n"
                     f"Reason: {cp.reason}\nNext action: {cp.next_action}\n"
                     f"Tests: {cp.tests}\nGit: {cp.git_commit}\n",encoding="utf-8")
