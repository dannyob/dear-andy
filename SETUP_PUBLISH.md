# Setting Up Publishing

The `publish/` directory is where `make publish` will copy generated HTML files. You have two options:

## Option 1: Symlink to Your Website (Recommended)

Create a symlink that points to your static website directory:

```bash
ln -s /Users/danny/Public/dannyob.eth/dear-andy publish
```

Now `make publish` will copy files directly to your website.

## Option 2: Regular Directory

Create a regular directory:

```bash
mkdir publish
```

Then manually copy or deploy files from `publish/` to your website.

## Workflow

1. Generate HTML: `make html`
2. Publish: `make publish`

The publish command will:
- Copy all `YYYY-MM-DD.html` files
- Copy `index.html`
- Copy the `images/` directory if it exists
- Preserve other files in the publish directory (won't delete anything)

## Note on `make clean`

The `make clean` command will NOT delete the `publish/` directory or symlink, so it's safe to run.
