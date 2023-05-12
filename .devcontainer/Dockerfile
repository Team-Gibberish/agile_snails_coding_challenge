FROM conda/miniconda3

# copy environment files
COPY environment.yml /home

# Create python environment
RUN conda env update -n base --file /home/environment.yml
RUN conda init
