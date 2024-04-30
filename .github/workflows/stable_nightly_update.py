on:
#  schedule:
#    - cron: '0 0 * * *' # Run daily at midnight
  pull_request:
    branches: [ "feature/update-ci" ]      

jobs:
  stable_nightly_update:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Merge develop into main
        if: github.ref == 'refs/heads/feature/update-ci'
        run: |
          git checkout main_test
          git pull origin main_test
          git merge origin/feature/update-ci --no-edit
          git push origin main_test
