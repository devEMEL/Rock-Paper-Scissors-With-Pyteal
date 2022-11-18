import algosdk from "algosdk";
/* eslint import/no-webpack-loader-syntax: off */
import approvalProgram from "raw-loader!../build/approval.teal";
// import clearProgram from "!!raw-loader!../build/clear.teal";
console.log(approvalProgram)

const algod_token = "BJ1LKKTDdJ8UINBHPsiFU1cB8QMULUlK10g0CYkP"
const algod_address = "https://testnet-algorand.api.purestake.io/ps2"
const purestake_token = {'X-Api-key': algod_token}

const algodClient = new algosdk.Algodv2(algod_token, algod_address, purestake_token);
console.log(algodClient)


// 1. CONVERT FROM TEAL TO PROGRAM BYTE

// 2. DEPLOY THE APPLICATION (GOAL APP CREATE)