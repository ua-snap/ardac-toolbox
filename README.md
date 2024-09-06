# ardac-toolbox

Notebooks, modules, and more to expose SNAP data holdings and the SNAP Data API.

## What is this?

This repository is a place to store notebooks, modules, widgets, and code that might be used in ARDAC. This repo is a work in progress and all content should considered incomplete.


### Running Jupyter from Chinook compute node

Here's how to run Jupyter on a compute node on Chinook! 

Here is [RCS's page](https://uaf-rcs.gitbook.io/uaf-rcs-hpc-docs/third-party-software/jupyter#running-jupyterlab-notebook-on-chinook) on it. I got it working with some modifications.

You can start a jupyter server from an interactive session or with a job script. Here is an example job script:

```
# jupyter.slurm
#!/bin/bash

#SBATCH --job-name="Jupyter Workspace"
#SBATCH --partition=debug
#SBATCH --ntasks=24
#SBATCH --tasks-per-node=24
#SBATCH --time=01:00:00
#SBATCH --output="Jupyter.%j"

module purge
module load slurm

# The eval "$(conda shell.bash hook)" insures that you can load you conda environment
eval "$(conda shell.bash hook)"
conda activate snap-geo

# Get info for SSH Tunnel, the node that you are on and your username
NODE=$(hostname -s)
USERNAME=$(whoami)

# Print tunneling instructions
echo "Instructions to create SSH tunnel. On your LOCAL machine run: "
echo "ssh $USERNAME@chinook04.alaska.edu -L 8888:$NODE:8888 -N"

# Run Jupyter Lab or Notebook
# If you just want to connect a notebook e.g. through VS code, you can just run the server
jupyter server --no-browser --port=8888 --ip=0.0.0.0

echo "Closing Jupyter"
```

Okay great, the above worked for me to run a job that starts a jupyter server. However, I was having trouble with getting logged into the server. No matter what I would set the password to, e.g. with 

```
jupyter server password
```

I would get confirmation that the password was changed, but I could not get logged in!

However, after I ran `jupyter server generate-config`, further use of `jupyter server password` seems to have worked. So, if you find that the password you are using is not working, you could try this first. 

Also, I did remove the `ServerApp.password` item from the `$HOME/.jupyter/jupyter_server_config.json` file - sure if that helped or not.

#### Connecting notebook

Now we can connect a local notebook to use the compute node's resources. 

Run the port forwarding as suggested:

e.g., for user `snapdata` on the `n0` node:

```
ssh snapdata@chinook04.alaska.edu -L 8888:n0:8888 -N
```

Then, open the notebook of interest, and from the kernel selection menu, choose "Existing Jupyter Server" and punch in the localhost URL of `http://localhost:8888`. You should then prompted for a password, then which kernel to use. you might be prompted for a password again upon running a cell in the notebook (this seems to happen fairly often for me) but after that, you should be cooking.

#### Other tips

Because the kernel is indeed running on a compute node, it inherits the environment from the jupyter server, which means the working directory is wherever you executed `jupyter server ...`. This means you *cannot import a local module / package*. For example, you will not be able to import from a script that is in the same local folder as that notebook, because the kernel is looking for something in the same folder as where you started the jupyter server on the Chinook filesyste. 

What seems to be working the best so far is to start the server from whatever project directory on Chinook you want to be able to work on, and have your VS Code window ssh'd into the directory, so you can be modifying files somewhere like a subdir in your `$HOME` but running those files with the Jupyter server active on the compute node. You just need to run the same port forwarding command from the login node: `ssh snapdata@chinook04.alaska.edu -L 8888:n0:8888 -N`.
