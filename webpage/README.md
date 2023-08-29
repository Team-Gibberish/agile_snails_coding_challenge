# Frontend Readme

This readme covers the typescript environment used to create client-side
javascript.

> 💡 For the webserver and API definitions, look at
> [`sjautobidder/webserver.py`](../sjautobidder/webserver.py)

The frontend is written in [Typescript](https://www.typescriptlang.org/), which
is a typed superset of javascript. Typescript compiles down to javascript
(including optimizations) for the browser.
[Rollup](https://rollupjs.org/guide/en/) is used to compile all generated
javascript into one bundle file, to save on space, and package all dependencies.
Rollup also performs it's own optimizations, including branch-shaking (removing
unused code).

The GUI components used for the frontend is [Shoelace](shoelace.style). These
are **not** served with the bundled javascript.

## Building the Frontend

1. You must have already installed [Node.js (includes npm)](https://nodejs.org/en/)
2. Navigate to the webpage folder (this folder)
3. Run `npm install -g yarn` to install [Yarn](https://yarnpkg.com/) globally
4. Run `yarn` to install required dependencies.
5. Use the following command to compile typescript, and then use rollup to
   create bundles: `yarn run tsc; yarn run rollup -c`
6. You should now have an updated `js/index.js` containing your new code.
7. Use the webserver to access the website
    1. [Make sure you have a working python development environment for this project](../CONTRIBUTING.md)
    2. Host the webserver
        - Use `python -m sjautobidder.webserver`
        - **Or** Use the Docker container *(involved needing to network containers)*
        - **Or** use gunicorn *(linux only, take a look at the [docker startup script](../dockerstart.sh))*
    3. Navigate to the website with your browser

> 💡 Compiling typescript may throw up errors, however, typescript is designed
> to always compile, and so it will still produce a result. We Highly Recommend
> reading any error output.

## Linting the Frontend

Linting is ran via [ESlint](https://eslint.org/). It is recommended to use an IDE that
supports this for automatically linting as you go.

Comments are linted in according to (TSDoc)[https://tsdoc.org/]
