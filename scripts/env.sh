# Source this in any script or shell: `. ~/team14/scripts/env.sh`
# ~/.bashrc returns early for non-interactive shells, so the Foundry
# credentials and the pixi PATH are missing in `ssh host "cmd"` and in cron.
eval "$(grep -E '^export (FOUNDRY|QUAY|NXF)' "$HOME/.bashrc")"
export PATH="$HOME/.pixi/bin:$HOME/.local/bin:$PATH"

REG=quay.io/apheris/oslo-hackathon
export IMG_RFD_AB="$REG:apheris-rfd4-proteina-v0.3.0-antibody-2026-10-30"
export IMG_RFD_HER2="$REG:apheris-rfd4-proteina-v0.3.0-her2-2026-11-07"
export IMG_RFD_HER2_NOVEL="$REG:apheris-rfd4-proteina-v0.3.0-her2-novel-2026-11-09"
export IMG_OF3="$REG:apheris-openfold3-v1.3.0"
export IMG_OF3_OB="$REG:apheris-openfold3-v1.3.0-of3ob"
export IMG_BOLTZ2="$REG:apheris-boltz-v1.3.0-boltz2"
export IMG_ESMFOLD2="$REG:apheris-esmfold2-v1.4.0-release"
export IMG_PROTENIX2="$REG:apheris-protenix-v1.3.0-v2"
export IMG_MSA="$REG:apheris-msa-v1.1.0"
export IMG_DATA="$REG:apheris-data-v1.2.0"

export TEAM_ROOT="$HOME/team14"
