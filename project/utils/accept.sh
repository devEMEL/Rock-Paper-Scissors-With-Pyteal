#!/usr/bin/env bash


APP_ID=124098211
ONE=HLDUXEOR44N3AHPEACVEKWOLXWEUORLDMR2HUTYXKL6EWSFI5P54NRF7IU
TWO=R4TAUMFDWOMY23ZACKQ5UPZWN73HFZOPZEQNWOWEOQQVBYVJLM7TVB4B2M
WAGER=123456
APP_ACCOUNT=PX6CLROBDK5HMKUQ33O3CPUXGGUN5FLQRUVYBT6U4AT46XYUGECSJEAEFQ

# create accept transaction
goal app call \
    --app-id "$APP_ID" \
    -f "$TWO" \
    --app-account "$ONE" \
    --app-arg "str:accept" \
    --app-arg "str:r" \
    -o accept-call.tx

# create wager transaction
goal clerk send \
    -a "$WAGER" \
    -t "$APP_ACCOUNT" \
    -f "$TWO" \
    -o accept-wager.tx

# group transactions
cat accept-call.tx accept-wager.tx > accept-combined.tx
goal clerk group -i accept-combined.tx -o accept-grouped.tx
goal clerk split -i accept-grouped.tx -o accept-split.tx

# sign individual transactions
goal clerk sign -i accept-split-0.tx -o accept-signed-0.tx
goal clerk sign -i accept-split-1.tx -o accept-signed-1.tx

# re-combine individually signed transactions
cat accept-signed-0.tx accept-signed-1.tx > accept-signed-final.tx

# send transaction
goal clerk rawsend -f accept-signed-final.tx