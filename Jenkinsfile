pipeline {
  agent any

  environment {
    IMAGE_TAG = '' // will be set later dynamically
  }

  stages {
    stage('Load Env from Credentials') {
      steps {
        withCredentials([
          string(credentialsId: 'AWS_REGION', variable: 'AWS_REGION'),
          string(credentialsId: 'ECR_REPO', variable: 'ECR_REPO'),
          string(credentialsId: 'GIT_REPO', variable: 'GIT_REPO'),
          string(credentialsId: 'AWS_ACCOUNT_ID', variable: 'AWS_ACCOUNT_ID'),
          string(credentialsId: 'GIT_AUTHOR_EMAIL', variable: 'AUTHOR_EMAIL'),
          string(credentialsId: 'GIT_AUTHOR_NAME', variable: 'AUTHOR_NAME')
        ]) {
          script {
            env.AWS_REGION = AWS_REGION
            env.ECR_REPO = ECR_REPO
            env.GIT_REPO = GIT_REPO
            env.AWS_ACCOUNT_ID = AWS_ACCOUNT_ID
            env.AUTHOR_EMAIL = AUTHOR_EMAIL
            env.AUTHOR_NAME = AUTHOR_NAME
          }
        }
      }
    }

    stage('Checkout Code') {
      steps {
        git url: "${env.GIT_REPO}", branch: 'main'
      }
    }

    stage('Build & Push Docker Image') {
      steps {
        script {
          def repoUri = "${env.ECR_REPO}"

          // Login to ECR
          bat """
            aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin ${repoUri}
          """

          // Fetch and parse image tags (uses PowerShell)
          def tagList = bat(
            script: """
              @echo off
              for /f "tokens=*" %%a in ('aws ecr list-images --repository-name %ECR_REPO% --region %AWS_REGION% --query "imageIds[*].imageTag" --output text') do echo %%a
            """,
            returnStdout: true
          ).trim().split()

          def numericTags = tagList.findAll { it ==~ /^\d+$/ }.collect { it.toInteger() }
          def nextTag = numericTags ? (numericTags.max() + 1) : 1
          env.IMAGE_TAG = "${nextTag}"

          echo "Building Docker Image with Tag: ${env.IMAGE_TAG}"

          bat """
            docker build -t ${repoUri}:${env.IMAGE_TAG} .
            docker tag ${repoUri}:${env.IMAGE_TAG} ${repoUri}:${env.IMAGE_TAG}
            docker push ${repoUri}:${env.IMAGE_TAG}
          """
        }
      }
    }

    // For now, leaving this block commented — it uses Unix-style commands like sed and needs a Windows equivalent
    // Let me know if you want this ported to PowerShell or Git Bash
    /*
    stage('Update GitOps Repo') {
      steps {
        script {
          def repoUri = "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.AWS_REGION}.amazonaws.com/${env.ECR_REPO}"
          bat """
            git clone ${env.GIT_REPO} gitops-temp
            cd gitops-temp

            powershell -Command "(Get-Content deployment.yaml) -replace 'image: .*', 'image: ${repoUri}:${env.IMAGE_TAG}' | Set-Content deployment.yaml"

            git config user.email "${env.AUTHOR_EMAIL}"
            git config user.name "${env.AUTHOR_NAME}"
            git commit -am "Update image tag to ${env.IMAGE_TAG}"
            git push origin main
          """
        }
      }
    }
    */
  }
}
