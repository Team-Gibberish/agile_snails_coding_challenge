FROM conda/miniconda3 as builder

# copy environment files
COPY environment.yml /home

# Create python environment
RUN conda env update -n base --file /home/environment.yml
RUN conda init

COPY sjautobidder /code/sjautobidder
COPY pyproject.toml /code/
COPY setup.cfg /code/
COPY README.md /code
WORKDIR /code
RUN python -m build .
RUN ls /code


FROM node as website_builder

#RUN npm install -g yarn
COPY webpage /webpage
WORKDIR /webpage
RUN yarn
RUN yarn run tsc; yarn run rollup -c

FROM conda/miniconda3

# --- Python Environment --- #

# copy environment files
COPY environment.yml /home

# Create python environment
RUN conda env update -n base --file /home/environment.yml
RUN conda init

# ------- autobidder ------- #

# copy pre-built sjautobidder module
# Remember to build with `python -m build .`

COPY --from=builder /code/dist /home/dist

# copy over webpage
# Remember to build with tsc and rollup
RUN mkdir /home/webpage/

# js dist
COPY --from=website_builder /webpage/js/ /home/webpage/js/

# html pages
COPY --from=website_builder /webpage/*.html /home/webpage/

# css
COPY --from=website_builder /webpage/css/ /home/webpage/css/

# img
COPY --from=website_builder /webpage/img/ /home/webpage/img/

# data
COPY --from=website_builder /webpage/data/ /home/webpage/data/

# Install sjautobidder
RUN python -m pip install /home/dist/sjautobidder-0.0.1-py3-none-any.whl

# ---- Docker Execution ---- #

# Copy execution script
COPY dockerstart.sh /home/start.sh
RUN chmod +x /home/start.sh

EXPOSE 80
ENTRYPOINT ["/home/start.sh"]
