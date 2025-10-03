# Build Directory

This directory contains all build artifacts and generated files.

## Structure

- `coverage/` - All coverage reports and data files
  - `html/` - HTML coverage reports
  - `coverage.xml` - XML coverage report
  - `coverage.json` - JSON coverage report
  - `.coverage*` - Coverage data files

- `reports/` - Test and build reports
  - `junit*.xml` - JUnit test reports

- `lib/` - Built Python packages (generated during build)
- `bdist.*/` - Binary distribution files (generated during build)

## Note

All files in this directory are generated and should not be committed to version control.
They are listed in `.gitignore`.