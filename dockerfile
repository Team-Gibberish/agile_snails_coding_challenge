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
COPY dist/ /home/dist

# copy over webpage
# Remember to build with tsc and rollup
RUN mkdir /home/webpage/

# js dist
COPY webpage/js/ /home/webpage/js/

# html pages
COPY webpage/*.html /home/webpage/

# css
COPY webpage/css/ /home/webpage/css/

# img
COPY webpage/img/ /home/webpage/img/

# data
COPY webpage/data/ /home/webpage/data/

# Install sjautobidder
RUN python -m pip install /home/dist/sjautobidder-0.0.1-py3-none-any.whl

# ---- Docker Execution ---- #

# Copy execution script
COPY dockerstart.sh /home/start.sh
RUN chmod +x /home/start.sh

EXPOSE 80
ENTRYPOINT ["/home/start.sh"]
