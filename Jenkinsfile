pipeline {
  agent any

  environment {
    IMAGE_TAG = ''
    ROLE_ARN = 'arn:aws:iam::420866608360:role/ECR_Push_Role' // ✅ Your role
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

    stage('Assume Role, Build & Push Docker Image') {
      steps {
        script {
          def repoUri = "${env.ECR_REPO}"

          // Full PowerShell wrapped inside bat to ensure Windows compatibility
          bat '''
          powershell -NoProfile -Command ^
            "$role = aws sts assume-role --role-arn 'arn:aws:iam::420866608360:role/ECR_Push_Role' --role-session-name 'jenkins-session' | ConvertFrom-Json; ^
            $env:AWS_ACCESS_KEY_ID = $role.Credentials.AccessKeyId; ^
            $env:AWS_SECRET_ACCESS_KEY = $role.Credentials.SecretAccessKey; ^
            $env:AWS_SESSION_TOKEN = $role.Credentials.SessionToken; ^

            aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REPO%; ^

            $tags = aws ecr list-images --repository-name %ECR_REPO% --region %AWS_REGION% --query 'imageIds[*].imageTag' --output text; ^
            $numTags = $tags -split ' ' | Where-Object { $_ -match '^[0-9]+$' } | ForEach-Object { [int]$_ }; ^
            $nextTag = ($numTags | Measure-Object -Maximum).Maximum + 1; ^
            if (!$nextTag) { $nextTag = 1 }; ^
            echo IMAGE_TAG=$nextTag > tag.txt; ^

            docker build -t %ECR_REPO%:$nextTag .; ^
            docker push %ECR_REPO%:$nextTag"
          '''
          
          // Read tag and use it in Jenkins
          def tagLine = readFile('tag.txt').trim()
          env.IMAGE_TAG = tagLine.tokenize('=')[1]
          echo "Successfully pushed Docker image with tag: ${env.IMAGE_TAG}"
        }
      }
    }
  }
}
