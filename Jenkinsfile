pipeline {
  agent any
  environment {
    PYTHON = 'python3'
    SONAR_HOST_URL = credentials('SONAR_HOST_URL')
    SONAR_TOKEN    = credentials('SONAR_TOKEN')
  }
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
    stage('Setup Python') {
      steps {
        sh '''
          set -euo pipefail
          ${PYTHON} -m venv .ci-venv
          . .ci-venv/bin/activate
          pip install -U pip ruff pytest
        '''
      }
    }
    stage('Lint') {
      steps {
        sh '''
          set -euo pipefail
          . .ci-venv/bin/activate
          ruff check services || true
        '''
      }
    }
    stage('Tests') {
      steps {
        sh '''
          set -euo pipefail
          . .ci-venv/bin/activate
          PYTHONPATH=services/submission-api pytest -q
        '''
      }
    }
    stage('Build Images') {
      steps {
        sh '''
          set -euo pipefail
          docker build -t cstr_submission_api:ci -f services/submission-api/Dockerfile services/submission-api
          docker build -t cstr_data_ingestor:ci -f services/data-ingestor/Dockerfile services/data-ingestor
          docker build -t cstr_validation_worker:ci -f services/validation-worker/Dockerfile services/validation-worker
        '''
      }
    }
    stage('Trivy Scan') {
      steps {
        sh '''
          set -euo pipefail
          docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.55.0 image --no-progress --severity HIGH,CRITICAL cstr_submission_api:ci || true
          docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.55.0 image --no-progress --severity HIGH,CRITICAL cstr_data_ingestor:ci || true
          docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.55.0 image --no-progress --severity HIGH,CRITICAL cstr_validation_worker:ci || true
        '''
      }
    }
    stage('SonarQube (optional)') {
      when { expression { return env.SONAR_HOST_URL && env.SONAR_TOKEN } }
      steps {
        sh '''
          set -euo pipefail
          docker run --rm -e SONAR_HOST_URL="${SONAR_HOST_URL}" -e SONAR_LOGIN="${SONAR_TOKEN}" \
            -v "$PWD:/usr/src" sonarsource/sonar-scanner-cli:5
        '''
      }
    }
  }
}
