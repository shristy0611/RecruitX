"""Machine learning model integration manager."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sklearn.base import BaseEstimator
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

from google.ai.generativelanguage_v1.types import content_pb2 as content
from google.ai.generativelanguage_v1.types import model_pb2 as model
from google.generativeai.types import model_types

logger = logging.getLogger(__name__)

@dataclass
class ModelMetadata:
    """Metadata for ML models."""
    model_id: str
    model_type: str
    version: str
    created_at: datetime
    metrics: Dict[str, float]
    parameters: Dict[str, Any]

class ModelManager:
    """Manages ML model integration with Gemini."""
    
    def __init__(
        self,
        models_dir: Union[str, Path],
        gemini_model: model_types.GenerativeModel,
        embedding_model: model_types.EmbeddingModel,
        cache_dir: Optional[Union[str, Path]] = None,
        max_retries: int = 3,
        batch_size: int = 32
    ):
        """Initialize manager.
        
        Args:
            models_dir: Directory for model storage
            gemini_model: Gemini model for text generation
            embedding_model: Gemini model for embeddings
            cache_dir: Cache directory for embeddings
            max_retries: Maximum API retries
            batch_size: Batch size for processing
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
        self.gemini = gemini_model
        self.embedding_model = embedding_model
        self.max_retries = max_retries
        self.batch_size = batch_size
        
        # Model registry
        self.models: Dict[str, Tuple[BaseEstimator, ModelMetadata]] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        
        # Load existing models
        self._load_models()
        
    def _load_models(self):
        """Load existing models from disk."""
        for model_path in self.models_dir.glob("*.joblib"):
            try:
                model_id = model_path.stem
                model_data = joblib.load(model_path)
                
                self.models[model_id] = (
                    model_data["model"],
                    model_data["metadata"]
                )
                if "scaler" in model_data:
                    self.scalers[model_id] = model_data["scaler"]
                    
                logger.info(f"Loaded model: {model_id}")
                
            except Exception as e:
                logger.error(f"Error loading model {model_path}: {e}")
                
    def _save_model(
        self,
        model_id: str,
        model: BaseEstimator,
        metadata: ModelMetadata,
        scaler: Optional[StandardScaler] = None
    ):
        """Save model to disk.
        
        Args:
            model_id: Model identifier
            model: Trained model
            metadata: Model metadata
            scaler: Optional scaler
        """
        model_path = self.models_dir / f"{model_id}.joblib"
        model_data = {
            "model": model,
            "metadata": metadata
        }
        if scaler is not None:
            model_data["scaler"] = scaler
            
        joblib.dump(model_data, model_path)
        logger.info(f"Saved model: {model_id}")
        
    async def create_skill_classifier(
        self,
        training_data: List[Dict[str, Any]],
        validation_split: float = 0.2
    ) -> str:
        """Create and train skill classifier model.
        
        Args:
            training_data: List of training examples
            validation_split: Validation split ratio
            
        Returns:
            Model ID
        """
        # Extract features using Gemini
        X = []
        y = []
        
        for example in training_data:
            features = await self._extract_skill_features(example)
            X.append(features)
            y.append(example["label"])
            
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y,
            test_size=validation_split,
            random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        # Train model
        model = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            activation="relu",
            solver="adam",
            max_iter=1000,
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train)
        val_score = model.score(X_val_scaled, y_val)
        
        # Create metadata
        model_id = f"skill_classifier_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        metadata = ModelMetadata(
            model_id=model_id,
            model_type="skill_classifier",
            version="1.0",
            created_at=datetime.now(),
            metrics={
                "train_accuracy": float(train_score),
                "val_accuracy": float(val_score)
            },
            parameters=model.get_params()
        )
        
        # Save model
        self.models[model_id] = (model, metadata)
        self.scalers[model_id] = scaler
        self._save_model(model_id, model, metadata, scaler)
        
        return model_id
        
    async def create_experience_regressor(
        self,
        training_data: List[Dict[str, Any]],
        validation_split: float = 0.2
    ) -> str:
        """Create and train experience level regressor.
        
        Args:
            training_data: List of training examples
            validation_split: Validation split ratio
            
        Returns:
            Model ID
        """
        # Extract features using Gemini
        X = []
        y = []
        
        for example in training_data:
            features = await self._extract_experience_features(example)
            X.append(features)
            y.append(example["years"])
            
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y,
            test_size=validation_split,
            random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        # Train model
        model = GaussianProcessRegressor(
            random_state=42,
            normalize_y=True
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train)
        val_score = model.score(X_val_scaled, y_val)
        
        # Create metadata
        model_id = f"experience_regressor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        metadata = ModelMetadata(
            model_id=model_id,
            model_type="experience_regressor",
            version="1.0",
            created_at=datetime.now(),
            metrics={
                "train_r2": float(train_score),
                "val_r2": float(val_score)
            },
            parameters=model.get_params()
        )
        
        # Save model
        self.models[model_id] = (model, metadata)
        self.scalers[model_id] = scaler
        self._save_model(model_id, model, metadata, scaler)
        
        return model_id
        
    async def create_education_classifier(
        self,
        training_data: List[Dict[str, Any]],
        validation_split: float = 0.2
    ) -> str:
        """Create and train education classifier model.
        
        Args:
            training_data: List of training examples
            validation_split: Validation split ratio
            
        Returns:
            Model ID
        """
        # Extract features using Gemini
        X = []
        y = []
        
        for example in training_data:
            features = await self._extract_education_features(example)
            X.append(features)
            y.append(example["level"])
            
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y,
            test_size=validation_split,
            random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        # Train model
        model = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            activation="relu",
            solver="adam",
            max_iter=1000,
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train)
        val_score = model.score(X_val_scaled, y_val)
        
        # Create metadata
        model_id = f"education_classifier_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        metadata = ModelMetadata(
            model_id=model_id,
            model_type="education_classifier",
            version="1.0",
            created_at=datetime.now(),
            metrics={
                "train_accuracy": float(train_score),
                "val_accuracy": float(val_score)
            },
            parameters=model.get_params()
        )
        
        # Save model
        self.models[model_id] = (model, metadata)
        self.scalers[model_id] = scaler
        self._save_model(model_id, model, metadata, scaler)
        
        return model_id
        
    async def predict(
        self,
        model_id: str,
        data: Dict[str, Any]
    ) -> Tuple[Any, float]:
        """Make prediction using specified model.
        
        Args:
            model_id: Model identifier
            data: Input data
            
        Returns:
            Tuple of prediction and confidence
        """
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
            
        model, metadata = self.models[model_id]
        scaler = self.scalers.get(model_id)
        
        # Extract features based on model type
        if metadata.model_type == "skill_classifier":
            features = await self._extract_skill_features(data)
        elif metadata.model_type == "experience_regressor":
            features = await self._extract_experience_features(data)
        elif metadata.model_type == "education_classifier":
            features = await self._extract_education_features(data)
        else:
            raise ValueError(f"Unknown model type: {metadata.model_type}")
            
        # Scale features if scaler exists
        X = np.array([features])
        if scaler is not None:
            X = scaler.transform(X)
            
        # Make prediction
        if isinstance(model, GaussianProcessRegressor):
            y_pred, std = model.predict(X, return_std=True)
            confidence = 1.0 / (1.0 + std[0])
            return float(y_pred[0]), float(confidence)
        else:
            y_pred = model.predict(X)
            proba = model.predict_proba(X)
            confidence = float(np.max(proba[0]))
            return y_pred[0], confidence
            
    async def _extract_skill_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Extract features for skill classification.
        
        Args:
            data: Input data
            
        Returns:
            Feature vector
        """
        # Get text embedding
        text = data.get("description", "")
        embedding = await self._get_embedding(text)
        
        # Get additional features from Gemini
        prompt = f"""Analyze the following text and extract numerical features for skill classification:
        Text: {text}
        
        Return a JSON object with these features:
        - technical_level (0-1): Technical complexity level
        - experience_required (0-1): Required experience level
        - specialization (0-1): Degree of specialization
        - soft_skills (0-1): Soft skills requirements
        """
        
        response = await self._retry_gemini_call(
            lambda: self.gemini.generate_content(prompt)
        )
        
        features = response.json()
        
        # Combine embedding and extracted features
        return np.concatenate([
            embedding,
            [
                features["technical_level"],
                features["experience_required"],
                features["specialization"],
                features["soft_skills"]
            ]
        ])
        
    async def _extract_experience_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Extract features for experience regression.
        
        Args:
            data: Input data
            
        Returns:
            Feature vector
        """
        # Get text embedding
        text = data.get("description", "")
        embedding = await self._get_embedding(text)
        
        # Get additional features from Gemini
        prompt = f"""Analyze the following text and extract numerical features for experience level prediction:
        Text: {text}
        
        Return a JSON object with these features:
        - role_seniority (0-1): Seniority level of the role
        - technical_depth (0-1): Required technical depth
        - leadership (0-1): Leadership requirements
        - project_complexity (0-1): Typical project complexity
        """
        
        response = await self._retry_gemini_call(
            lambda: self.gemini.generate_content(prompt)
        )
        
        features = response.json()
        
        # Combine embedding and extracted features
        return np.concatenate([
            embedding,
            [
                features["role_seniority"],
                features["technical_depth"],
                features["leadership"],
                features["project_complexity"]
            ]
        ])
        
    async def _extract_education_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Extract features for education classification.
        
        Args:
            data: Input data
            
        Returns:
            Feature vector
        """
        # Get text embedding
        text = data.get("description", "")
        embedding = await self._get_embedding(text)
        
        # Get additional features from Gemini
        prompt = f"""Analyze the following text and extract numerical features for education level classification:
        Text: {text}
        
        Return a JSON object with these features:
        - academic_level (0-1): Required academic level
        - research_focus (0-1): Research/theoretical focus
        - practical_skills (0-1): Practical skills requirements
        - certification_needs (0-1): Professional certification requirements
        """
        
        response = await self._retry_gemini_call(
            lambda: self.gemini.generate_content(prompt)
        )
        
        features = response.json()
        
        # Combine embedding and extracted features
        return np.concatenate([
            embedding,
            [
                features["academic_level"],
                features["research_focus"],
                features["practical_skills"],
                features["certification_needs"]
            ]
        ])
        
    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get text embedding from cache or Gemini.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        if not text:
            return np.zeros(1024)  # Default embedding size
            
        # Check cache
        if self.cache_dir:
            cache_key = str(hash(text))
            cache_path = self.cache_dir / f"{cache_key}.npy"
            
            if cache_path.exists():
                return np.load(cache_path)
                
        # Get embedding from Gemini
        embedding = await self._retry_gemini_call(
            lambda: self.embedding_model.embed_content(text)
        )
        
        embedding_array = np.array(embedding.values)
        
        # Cache result
        if self.cache_dir:
            np.save(cache_path, embedding_array)
            
        return embedding_array
        
    async def _retry_gemini_call(self, call):
        """Retry Gemini API call with exponential backoff.
        
        Args:
            call: API call function
            
        Returns:
            API response
        """
        for attempt in range(self.max_retries):
            try:
                return await call()
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                    
                delay = 2 ** attempt
                logger.warning(
                    f"Gemini API call failed (attempt {attempt + 1}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay) 