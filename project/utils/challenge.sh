#!/usr/bin/env bash


APP_ID=124098211
ONE=HLDUXEOR44N3AHPEACVEKWOLXWEUORLDMR2HUTYXKL6EWSFI5P54NRF7IU
TWO=R4TAUMFDWOMY23ZACKQ5UPZWN73HFZOPZEQNWOWEOQQVBYVJLM7TVB4B2M



goal app call \
    --app-id "$APP_ID" \
    -f "$ONE" \
    --app-account R4TAUMFDWOMY23ZACKQ5UPZWN73HFZOPZEQNWOWEOQQVBYVJLM7TVB4B2M \
    --app-arg "str:challenge" \
    --app-arg "b64:BDpxh3TFcr2KJa2+sb/NXAJWrhHOz5+cP5JdDlK+r4k=" \
    -o challenge-call.tx

goal clerk send \
    -a 123456 \
    -t PX6CLROBDK5HMKUQ33O3CPUXGGUN5FLQRUVYBT6U4AT46XYUGECSJEAEFQ \
    -f "$ONE" \
    -o challenge-wager.tx

# group transactions
cat challenge-call.tx challenge-wager.tx > challenge-combined.tx
goal clerk group -i challenge-combined.tx -o challenge-grouped.tx
goal clerk split -i challenge-grouped.tx -o challenge-split.tx

# sign individual transactions
goal clerk sign -i challenge-split-0.tx -o challenge-signed-0.tx
goal clerk sign -i challenge-split-1.tx -o challenge-signed-1.tx

# re-combine individually signed transactions
cat challenge-signed-0.tx challenge-signed-1.tx > challenge-signed-final.tx

# send transaction
goal clerk rawsend -f challenge-signed-final.tx