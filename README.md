# team 14 (umi-zoomi) working area

Shared VM, one user, one H100. Everything below is about not stepping on
each other.

## First thing, every session

    . ~/team14/scripts/env.sh

That loads the Foundry credentials and the pixi PATH (plain `ssh host "cmd"`
misses them) and sets $IMG_* for every model image.

## Rules

1. **Your own scratch** goes in `people/<yourname>/`. Shared inputs go in
   `data/`, shared results in `runs/`.
2. **Never run a GPU job bare.** Wrap it:

       ~/team14/scripts/gpurun mohamed docker run --rm --gpus all ...

   It takes a lock so two jobs never share the card. Check first with
   `~/team14/scripts/gpu.sh`.
3. **One directory per run**, made by `newrun`:

       DIR=$(~/team14/scripts/newrun mohamed rfd-antibody-50)

   Fill in its `NOTE.md` while the job runs. The model also drops a
   `config.json` in its output dir; keep it, that is the reproducibility
   evidence.
4. **Write the reason down** in `notes/DECISIONS.md` as you decide, and the
   numbers in `notes/SCORES.md`. 40 % of the score is why, not what.
5. **Long jobs go in tmux**, or they die when your laptop sleeps:

       tmux new -s mohamed      # start
       tmux attach -t mohamed   # come back
       tmux ls                  # see everyone's sessions

   We share one user, so anyone can attach to anyone's session. That is the
   cheapest way to pair on a problem or take over a job.

## The pipeline

    design          generate (--num-replicates up to 200, --seed, --model)
    metrics         native RFD4 scoring
    refold-prepare  pick the best (--top-n), write cofolding queries
    openfold3 predict   refold them
    refold-score    pass criteria (--criterion antibody)

OpenFold3 has to be in the pipeline to qualify for the money prize.

## Shape of a run

    . ~/team14/scripts/env.sh
    DIR=$(~/team14/scripts/newrun mohamed first-design)
    ~/team14/scripts/gpurun mohamed \
      docker run --rm --gpus all -v "$DIR":/work -v ~/team14/data:/data \
      "$IMG_RFD_AB" module-run design \
        --input /data/target.cif --output /work/designs \
        --model antibody --num-replicates 50 --seed 1 \
        --recycle-strategy high/front_loaded
