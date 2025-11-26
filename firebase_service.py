"""
Firebase Service for storing search results and metadata
Uses Firebase Firestore (NoSQL database)
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

load_dotenv()


class FirebaseService:
    """
    Service for interacting with Firebase Firestore
    Stores search metadata and results
    """

    def __init__(self):
        """Initialize Firebase connection"""
        self.db = None
        self._initialized = False
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Option 1: Use service account file
                service_account_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
                if service_account_path:
                    # Try to resolve relative paths
                    if not os.path.isabs(service_account_path):
                        # Try relative to current directory
                        if not os.path.exists(service_account_path):
                            # Try relative to backend directory
                            backend_dir = os.path.dirname(os.path.abspath(__file__))
                            alt_path = os.path.join(backend_dir, service_account_path)
                            if os.path.exists(alt_path):
                                service_account_path = alt_path
                            else:
                                # Try just the filename in backend directory
                                filename = os.path.basename(service_account_path)
                                alt_path = os.path.join(backend_dir, filename)
                                if os.path.exists(alt_path):
                                    service_account_path = alt_path

                    if os.path.exists(service_account_path):
                        try:
                            cred = credentials.Certificate(service_account_path)
                            firebase_admin.initialize_app(cred)
                            print(
                                f"Firebase initialized from file: {service_account_path}"
                            )
                        except Exception as e:
                            print(f"Error loading Firebase credentials from file: {e}")
                            raise
                else:
                    # Option 2: Use service account JSON from environment variable
                    service_account_json = os.environ.get(
                        "FIREBASE_SERVICE_ACCOUNT_JSON"
                    )
                    if service_account_json:
                        try:
                            # Try to parse as JSON string first
                            if isinstance(service_account_json, str):
                                # Remove any extra whitespace/newlines at start/end only
                                service_account_json = service_account_json.strip()

                                # Log first 100 chars for debugging (without exposing secrets)
                                print(
                                    f"Firebase JSON length: {len(service_account_json)} chars"
                                )
                                print(
                                    f"Firebase JSON starts with: {service_account_json[:50]}..."
                                )

                                # If it looks like a JSON string, parse it
                                if service_account_json.startswith("{"):
                                    cred_dict = json.loads(service_account_json)

                                    # Validate required fields
                                    required_fields = [
                                        "type",
                                        "project_id",
                                        "private_key",
                                        "client_email",
                                    ]
                                    missing_fields = [
                                        f for f in required_fields if f not in cred_dict
                                    ]
                                    if missing_fields:
                                        raise ValueError(
                                            f"Missing required fields in Firebase JSON: {missing_fields}"
                                        )

                                    # Ensure private_key has proper format
                                    if "private_key" in cred_dict:
                                        private_key = cred_dict["private_key"]
                                        # Remove any trailing whitespace/newlines that might cause issues
                                        private_key = private_key.rstrip()
                                        # Ensure it ends with the proper marker
                                        if not private_key.endswith(
                                            "-----END PRIVATE KEY-----"
                                        ):
                                            # Try to fix it
                                            if (
                                                "-----END PRIVATE KEY-----"
                                                in private_key
                                            ):
                                                # Extract up to and including the end marker
                                                end_marker = "-----END PRIVATE KEY-----"
                                                idx = private_key.rfind(end_marker)
                                                if idx != -1:
                                                    private_key = private_key[
                                                        : idx + len(end_marker)
                                                    ]
                                                    cred_dict["private_key"] = (
                                                        private_key
                                                    )
                                                    print(
                                                        "Fixed private_key trailing characters"
                                                    )

                                        if not private_key.startswith("-----BEGIN"):
                                            raise ValueError(
                                                "Invalid private_key format in Firebase JSON"
                                            )

                                    print(
                                        f"Firebase JSON parsed successfully. Project: {cred_dict.get('project_id', 'unknown')}"
                                    )

                                else:
                                    # Might be a file path
                                    if os.path.exists(service_account_json):
                                        with open(service_account_json, "r") as f:
                                            cred_dict = json.load(f)
                                    else:
                                        raise ValueError(
                                            "FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON and file doesn't exist"
                                        )

                                cred = credentials.Certificate(cred_dict)
                                firebase_admin.initialize_app(cred)
                                print("Firebase initialized from environment variable")
                            else:
                                raise ValueError(
                                    "FIREBASE_SERVICE_ACCOUNT_JSON must be a string"
                                )
                        except json.JSONDecodeError as e:
                            print(f"Error parsing FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
                            print(
                                f"JSON error at position: {e.pos if hasattr(e, 'pos') else 'unknown'}"
                            )
                            print("Make sure the JSON is valid and in a single line")
                            # Log a sample of where the error occurred
                            if hasattr(e, "pos") and e.pos < len(service_account_json):
                                start = max(0, e.pos - 50)
                                end = min(len(service_account_json), e.pos + 50)
                                print(
                                    f"Context around error: ...{service_account_json[start:end]}..."
                                )
                            raise
                        except Exception as e:
                            print(f"Error initializing Firebase from JSON: {e}")
                            print(f"Error type: {type(e).__name__}")
                            print(
                                "Please verify FIREBASE_SERVICE_ACCOUNT_JSON is correctly formatted"
                            )
                            import traceback

                            traceback.print_exc()
                            raise
                    else:
                        # Option 3: Use default credentials (for Google Cloud environments)
                        try:
                            firebase_admin.initialize_app()
                            print("Firebase initialized with default credentials")
                        except Exception as e:
                            print(f"Warning: Firebase not configured. Error: {e}")
                            print(
                                "Results will not be saved. Please configure FIREBASE_SERVICE_ACCOUNT_PATH or FIREBASE_SERVICE_ACCOUNT_JSON"
                            )
                            return

            self.db = firestore.client()
            self._initialized = True
            print("Firebase Firestore client initialized successfully")

        except Exception as e:
            print(f"Warning: Could not initialize Firebase: {e}")
            print(
                "Results will not be saved to Firebase. Please configure FIREBASE_SERVICE_ACCOUNT_PATH or FIREBASE_SERVICE_ACCOUNT_JSON"
            )
            self.db = None
            self._initialized = False

    async def save_search_metadata(self, search_id: str, metadata: Dict):
        """Save search metadata to Firestore"""
        if not self.db:
            print("Firebase not available, skipping metadata save")
            return

        if not search_id or not metadata:
            print("Warning: Invalid search_id or metadata provided")
            return

        try:
            # Validate required fields
            required_fields = ["search_id", "status", "created_at"]
            for field in required_fields:
                if field not in metadata:
                    print(f"Warning: Missing required field '{field}' in metadata")

            doc_ref = self.db.collection("searches").document(search_id)
            doc_ref.set(metadata, merge=False)
            print(f"Search metadata saved: {search_id}")
        except Exception as e:
            print(f"Error saving search metadata: {e}")
            raise

    async def save_search_results(self, search_id: str, results: List[Dict]):
        """Save search results to Firestore"""
        if not self.db:
            print("Firebase not available, skipping results save")
            return

        if not search_id:
            print("Warning: Invalid search_id provided")
            return

        if not results:
            print("Warning: No results to save")
            return

        try:
            # Save results in a subcollection
            results_ref = (
                self.db.collection("searches").document(search_id).collection("results")
            )

            batch = self.db.batch()
            saved_count = 0

            for i, result in enumerate(results):
                # Validate result has required fields
                if not result.get("id"):
                    result["id"] = f"result_{i}"

                doc_ref = results_ref.document(result["id"])
                result["search_id"] = search_id
                result["saved_at"] = datetime.now().isoformat()

                # Ensure all fields are serializable
                clean_result = self._clean_dict_for_firestore(result)
                batch.set(doc_ref, clean_result)
                saved_count += 1

                # Commit in batches of 500 (Firestore limit)
                if (i + 1) % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
                    print(f"Saved batch: {i + 1} results")

            # Commit remaining
            if len(results) % 500 != 0:
                batch.commit()

            print(
                f"Successfully saved {saved_count} results to Firebase for search: {search_id}"
            )

        except Exception as e:
            print(f"Error saving search results: {e}")
            raise

    def _clean_dict_for_firestore(self, data: Dict) -> Dict:
        """Clean dictionary to ensure all values are Firestore-compatible"""
        cleaned = {}
        for key, value in data.items():
            if value is None:
                continue
            elif isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
            elif isinstance(value, dict):
                cleaned[key] = self._clean_dict_for_firestore(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    (
                        self._clean_dict_for_firestore(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                # Convert other types to string
                cleaned[key] = str(value)
        return cleaned

    async def update_search_status(
        self,
        search_id: str,
        status: str,
        results_count: int,
        error: Optional[str] = None,
    ):
        """Update search status"""
        if not self.db:
            return

        try:
            doc_ref = self.db.collection("searches").document(search_id)
            update_data = {
                "status": status,
                "results_count": results_count,
                "updated_at": datetime.now().isoformat(),
            }
            if error:
                update_data["error"] = error
            doc_ref.update(update_data)
        except Exception as e:
            print(f"Error updating search status: {e}")

    async def get_search_status(self, search_id: str) -> Optional[Dict]:
        """Get search status and metadata"""
        if not self.db:
            return None

        try:
            doc_ref = self.db.collection("searches").document(search_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting search status: {e}")
            return None

    async def get_search_results(
        self, search_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict]:
        """Get search results with pagination"""
        if not self.db:
            return []

        try:
            results_ref = (
                self.db.collection("searches")
                .document(search_id)
                .collection("results")
                .order_by("relevance_score", direction=firestore.Query.DESCENDING)
                .offset(offset)
                .limit(limit)
            )

            docs = results_ref.stream()
            results = [doc.to_dict() for doc in docs]
            return results

        except Exception as e:
            print(f"Error getting search results: {e}")
            return []

    async def list_recent_searches(self, limit: int = 20) -> List[Dict]:
        """List recent searches"""
        if not self.db or not self._initialized:
            print("Firebase not available, returning empty list")
            return []

        try:
            # Use asyncio timeout to prevent hanging
            searches_ref = (
                self.db.collection("searches")
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )

            # Convert sync stream to async with timeout
            def get_docs():
                try:
                    docs = searches_ref.stream()
                    return [doc.to_dict() for doc in docs]
                except Exception as e:
                    print(f"Error in get_docs: {e}")
                    return []

            # Run in executor with timeout
            loop = asyncio.get_event_loop()
            searches = await asyncio.wait_for(
                loop.run_in_executor(None, get_docs), timeout=5.0  # 5 second timeout
            )
            return searches

        except asyncio.TimeoutError:
            print("Timeout listing searches from Firebase (5s)")
            return []
        except Exception as e:
            print(f"Error listing searches: {e}")
            return []

    async def delete_search(self, search_id: str):
        """Delete a search and all its results"""
        if not self.db:
            return

        try:
            # Delete all results first
            results_ref = (
                self.db.collection("searches").document(search_id).collection("results")
            )

            batch = self.db.batch()
            count = 0
            for doc in results_ref.stream():
                batch.delete(doc.reference)
                count += 1
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()

            if count % 500 != 0:
                batch.commit()

            # Delete search document
            self.db.collection("searches").document(search_id).delete()

        except Exception as e:
            print(f"Error deleting search: {e}")
