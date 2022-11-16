
from pyteal import *

def approval_program():

	# locals
	local_opponent = Bytes("opponent")  # byteslice
	local_wager = Bytes("wager")  # uint64
	local_commitment = Bytes("commitment")  # byteslice
	local_reveal = Bytes("reveal")  # byteslice

	op_challenge = Bytes("challenge")
	op_accept = Bytes("accept")
	op_reveal = Bytes("reveal")

	init = Seq([
		Approve()
	])

	@Subroutine(TealType.none)
	def reset(account: Expr):
		return Seq(
			App.localPut(account, local_opponent, Bytes("")),
			App.localPut(account, local_wager, Int(0)),
			App.localPut(account, local_commitment, Bytes("")),
			App.localPut(account, local_reveal, Bytes("")),
	)

	no_op=Seq(
		Cond(
			[Txn.application_args[0] == op_challenge, create_challenge(),],
			[Txn.application_args[0] == op_accept, accept_challenge(),],
			[Txn.application_args[0] == op_reveal, reveal(),],
		),
		Reject(),
  ),

	return Cond(
		[Txn.application_id() == Int(0), init],
		# [Txn.on_completion() == OnComplete.DeleteApplication, delete],
		# [Txn.on_completion() == OnComplete.UpdateApplication, update],
		[Txn.on_completion() == OnComplete.OptIn, reset(Int(0))],
		# [Txn.on_completion() == OnComplete.CloseOut, close_out],
		[Txn.on_completion() == OnComplete.NoOp, no_op],
  )



def clear():
    return Approve()


