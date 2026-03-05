name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Create zip
        run: |
          zip -r spot_scheduler.zip custom_components/spot_scheduler

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: spot_scheduler.zip
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
