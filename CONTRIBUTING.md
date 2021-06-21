# Contributing to the IGWN Metapackages project

This page outlines the recommended procedure for contributing changes
to the IGWN Metapackages.
Please read the introduction to
[GitLab on git.ligo.org](https://computing.docs.ligo.org/guide/services/gitlab/)
before you start.

Note: this document can be viewed online
[here](https://packaging.docs.ligo.org/metapackages/guide/).

<!-- INCLUDE -->

## Reporting Issues

If you have a GitLab account, please report issues directly through gitlab.
Otherwise, you can use the service desk address
<mailto:contact+packaging-metapackages-602-issue-@support.ligo.org>
to send bug reports by e-mail.

In either case, please include as much detail as possible to reproduce the error,
including information about your operating system and the commands you used that
led you to the error.
If possible, please include a brief, self-contained code example that demonstrates the problem.

Note that when an issue is marked as 'confidential',
currently this means that most internal users will also not be able to see it,
but only a small number of people with reporter, developer or maintainer status.

## Contributing to the metapackages

All contributions to the IGWN Metpackages configuration must be made using the
fork and
[merge request](https://git.ligo.org/help/user/project/merge_requests/index.md)
[workflow](https://git.ligo.org/help/user/project/repository/forking_workflow.md),
which must then be reviewed by one of the project maintainers.

If you wish to contribute new code, or changes to existing code, please
follow this development workflow:

### Make a fork (copy) of `packaging/metpackages`

**You only need to do this once**

1. Go to the
   [IGWN Metapackages repository home page](https://git.ligo.org/packaging/metapackages/)
2. Click on the *Fork* button, that should lead you
   [here](https://git.ligo.org/packaging/metapackages/-/forks/new)
3. Select the namespace that you want to create the fork in, this will
   usually be your personal namespace

If you can't see the *Fork* button, make sure that you are logged in by
checking for your account profile photo in the top right-hand corner of the
screen.

### Clone your fork

Then, clone your fork with

```bash
git clone git@git.ligo.org:<namespace>/metapackages.git
```

### Keeping your fork up to date

Link your clone to the main (`upstream`) repository so that you can `fetch`
and `pull` changes, `merge` them with your clone, and `push` them to your
fork.
Do *not* make changes on your master branch.

1.  Link your fork to the main repository:

    ```bash
    cd metapackages
    git remote add upstream git@git.ligo.org:packaging/metapackages.git
    ```

    You need only do this step once.

2.  Update your `master` branch to track changes from upstream:

    ```bash
    git checkout master
    git fetch upstream
    git branch --set-upstream-to upstream/master
    git pull
    ```

    You only need to do this step once.

### Making changes

All changes should be developed on a feature branch in order to keep them
separate from other work, thus simplifying the review and merge once the
work is complete.
The workflow is:

1.  Create a new feature branch configured to track the `master` branch:

    ```bash
    git checkout master
    git pull
    git checkout -b my-new-feature upstream/master
    ```

    This command creates the new branch `my-new-feature`, sets up tracking the
    `upstream` repository, and checks out the new branch.
    There are other ways to do these steps, but this is a good habit since it will
    allow you to `fetch` and `merge` changes from `upstream/master` directly onto the branch.

2.  Develop the changes you would like to introduce, using `git commit` to
    finalise a specific change.
    Ideally commit small units of change often, rather than creating one large
    commit at the end, this will simplify review and make modifying any
    changes easier.

    Commit messages should be clear, identifying which code was changed, and why.
    Common practice is to use a short summary line (<50 characters), followed
    by a blank line, then more information in longer lines.

    !!! warning "Always include a changelog entry"
        All changes to any of the metapackages must include a changelog entry
        inserted at the **top** of the existing changelog.
        This new entry must include a timestamp in the correct format, and should
        have a `version` that matches the timestamp.

2.  Push your changes to the remote copy of your fork on <https://git.ligo.org>.
    The first `push` of any new feature branch will require the
    `-u/--set-upstream` option to `push` to create a link between your new
    branch and the `origin` remote:

    ```bash
    git push --set-upstream origin my-new-feature
    ```

    Subsequent pushes can be made with just:

    ```bash
    git push
    ```

3.  Keep your feature branch up to date with the `upstream` repository by doing:

    ```bash
    git pull --rebase upstream master
    git push --force origin my-new-feature
    ```

    This works if you created your branch with the `checkout` command above.
    If you forgot to add the `upstream/master` starting point, then you will
    need to dig deeper into git commands to get changes and merge them into
    your feature branch.

    If there are conflicts between `upstream` changes and your changes, you
    will need to resolve them before pushing everything to your fork.

### Open a merge request

When you feel that your work is finished, you should create a merge request
to propose that your changes be merged into the main (`upstream`) repository.

After you have pushed your new feature branch to `origin`, you should find a
new button on the
[IGWN Metapackages repository home page](https://git.ligo.org/packaging/metapackages/)
inviting you to create a merge request out of your newly pushed branch.
(If the button does not exist, you can initiate a merge request by going to
the `Merge Requests` tab on your fork website on git.ligo.org and clicking
`New merge request`)

You should click the button, and proceed to fill in the title and description
boxes on the merge request page.
It is recommended that you check the box to `Remove source branch when merge
request is accepted`; this will result in the branch being automatically
removed from your fork when the merge request is accepted.

Once the request has been opened, one of the maintainers will assign someone
to review the change.
There may be suggestions and/or discussion with the reviewer.
These interactions are intended to make the resulting changes better.
The reviewer will merge your request.

Once the changes are merged into the upstream repository, you should remove
the development branch from your clone using

```bash
git branch -d my-new-feature
```

A feature branch should *not* be repurposed for further development as this
can result in problems merging upstream changes.
