# Repository Separation Checklist

## Pre-Separation

- [ ] All tests passing
- [ ] Security scan complete
- [ ] Documentation up-to-date
- [ ] Version numbers consistent
- [ ] Git history clean
- [ ] Create backup of monorepo
- [ ] Notify team/stakeholders

## Repository Creation

### dartserver-core
- [ ] Create GitHub repository
- [ ] Set description and keywords
- [ ] Enable Actions
- [ ] Add collaborators
- [ ] Push initial commit
- [ ] Create release v1.0.0

### dartserver-games
- [ ] Create GitHub repository
- [ ] Set description and keywords
- [ ] Enable Actions
- [ ] Add collaborators
- [ ] Push initial commit
- [ ] Create release v1.0.0

### dartserver-services
- [ ] Create GitHub repository
- [ ] Set description and keywords
- [ ] Enable Actions
- [ ] Add collaborators
- [ ] Push initial commit
- [ ] Create release v1.0.0

### dartserver-app
- [ ] Create GitHub repository
- [ ] Set description and keywords
- [ ] Enable Actions
- [ ] Add collaborators
- [ ] Push initial commit
- [ ] Create release v1.0.0

## PyPI Publishing

- [ ] dartserver-core published
- [ ] dartserver-games published
- [ ] dartserver-services published
- [ ] dartserver-app published
- [ ] Verify all on PyPI
- [ ] Test pip install

## Main Repository Update

- [ ] Add git submodules
- [ ] Update README
- [ ] Update CI/CD workflows
- [ ] Test cloning with submodules
- [ ] Update documentation

## Post-Separation

- [ ] Update GitHub team permissions
- [ ] Setup branch protection rules
- [ ] Enable automated workflows
- [ ] Archive monorepo (or mark as coordinator)
- [ ] Update external references
- [ ] Announce to users
- [ ] Monitor for issues
