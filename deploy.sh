#!/usr/bin/env bash
# Safe to re-run: sets up the bucket and identity if missing, then deploys.
# Settings come from .env (copy env.example) or from the environment.
set -euo pipefail

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

for name in PROJECT REGION SERVICE BUCKET_NAME; do
  if [ -z "${!name:-}" ]; then
    echo "Missing setting: $name. Copy env.example to .env and fill it in." >&2
    exit 1
  fi
done

SA="$SERVICE@$PROJECT.iam.gserviceaccount.com"

gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com storage.googleapis.com iam.googleapis.com --project "$PROJECT"

gcloud storage buckets describe "gs://$BUCKET_NAME" --project "$PROJECT" >/dev/null 2>&1 ||
  gcloud storage buckets create "gs://$BUCKET_NAME" --project "$PROJECT" --location "$REGION" \
    --uniform-bucket-level-access --public-access-prevention

gcloud iam service-accounts describe "$SA" --project "$PROJECT" >/dev/null 2>&1 ||
  gcloud iam service-accounts create "$SERVICE" --project "$PROJECT" \
    --display-name "Message page service"

# Read access on this bucket only, nothing at project level.
# A brand-new service account takes a few seconds to become visible to GCS.
for attempt in 1 2 3 4 5 6; do
  gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" --project "$PROJECT" \
    --member "serviceAccount:$SA" --role roles/storage.objectViewer >/dev/null && break
  [ "$attempt" -eq 6 ] && exit 1
  sleep 10
done

gcloud run deploy "$SERVICE" --source . --project "$PROJECT" --region "$REGION" \
  --service-account "$SA" --set-env-vars "BUCKET_NAME=$BUCKET_NAME" \
  --allow-unauthenticated --min-instances 0 --max-instances 2 --memory 256Mi --quiet
