"""Production Model Registry and Lifecycle Management.

Tracks:
- Model versions, artifact serialization, and metadata
- Staging transitions (DEVELOPMENT -> STAGING -> PRODUCTION -> ARCHIVED)
- Performance metrics history (WAPE, MAE, Bias) and feature signatures
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import joblib


class ModelRegistry:
    """Manages versioned ML artifacts and stage transitions."""

    def __init__(self, registry_dir: str = "dukaanos/models"):
        self.registry_dir = registry_dir
        self.artifacts_dir = os.path.join(registry_dir, "artifacts")
        self.manifest_file = os.path.join(registry_dir, "model_registry.json")
        os.makedirs(self.artifacts_dir, exist_ok=True)
        self._ensure_manifest()

    def _ensure_manifest(self):
        """Initializes empty JSON registry manifest if not present."""
        if not os.path.exists(self.manifest_file):
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump({"models": []}, f, indent=2)

    def _read_manifest(self) -> Dict[str, Any]:
        """Reads registry manifest."""
        with open(self.manifest_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_manifest(self, manifest: Dict[str, Any]):
        """Persists registry manifest."""
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    def register_model(
        self,
        model_obj: Any,
        model_name: str,
        version: str,
        metrics: Dict[str, float],
        feature_names: List[str],
        stage: str = "PRODUCTION",
        description: str = "LightGBM Demand Forecaster",
    ) -> Dict[str, Any]:
        """Serializes model artifact and registers entry in manifest."""
        artifact_filename = f"{model_name}_v{version}.joblib"
        artifact_path = os.path.join(self.artifacts_dir, artifact_filename)

        # Save binary artifact
        joblib.dump(model_obj, artifact_path)

        manifest = self._read_manifest()

        # If promoting to PRODUCTION, demote previous production version of same model to ARCHIVED
        if stage == "PRODUCTION":
            for m in manifest["models"]:
                if m["model_name"] == model_name and m["stage"] == "PRODUCTION":
                    m["stage"] = "ARCHIVED"

        entry = {
            "model_name": model_name,
            "version": version,
            "stage": stage,
            "description": description,
            "metrics": metrics,
            "feature_names": feature_names,
            "artifact_path": artifact_path,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Replace existing version if already registered, else append
        manifest["models"] = [m for m in manifest["models"] if not (m["model_name"] == model_name and m["version"] == version)]
        manifest["models"].append(entry)
        self._write_manifest(manifest)

        return entry

    def load_production_model(self, model_name: str) -> Optional[tuple[Any, Dict[str, Any]]]:
        """Loads active PRODUCTION model artifact and metadata."""
        manifest = self._read_manifest()
        prod_entry = next((m for m in manifest["models"] if m["model_name"] == model_name and m["stage"] == "PRODUCTION"), None)

        if not prod_entry or not os.path.exists(prod_entry["artifact_path"]):
            return None

        model_obj = joblib.load(prod_entry["artifact_path"])
        return model_obj, prod_entry

    def list_models(self) -> List[Dict[str, Any]]:
        """Returns all registered model entries."""
        return self._read_manifest().get("models", [])

