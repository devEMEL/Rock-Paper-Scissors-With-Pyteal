from pyteal import *
from pyteal.types import TealType
from pyteal.ast.bytes import Bytes
from pyteal.ast.expr import Expr

def approval_program():

	# locals
	local_opponent = Bytes("opponent")  # byteslice
	local_wager = Bytes("wager")  # uint64
	local_commitment = Bytes("commitment")  # byteslice
	local_reveal = Bytes("reveal")  # byteslice

	op_challenge = Bytes("challenge")
	op_accept = Bytes("accept")
	op_reveal = Bytes("reveal")



	@Subroutine(TealType.none)
	def reset(account: Expr):
		return Seq(
			App.localPut(account, local_opponent, Bytes("")),
			App.localPut(account, local_wager, Int(0)),
			App.localPut(account, local_commitment, Bytes("")),
			App.localPut(account, local_reveal, Bytes(""))
		)

	@Subroutine(TealType.none)
	def create_challenge():
		return Reject()

	@Subroutine(TealType.none)
	def accept_challenge():
		return Reject()

	@Subroutine(TealType.none)
	def reveal():
		return Reject()


	init = Seq([
		Approve()
	])

	opt_in=Seq([
		reset(Int(0)),
		Approve()
	])

	no_op=Seq(
		Cond(
			[Txn.application_args[0] == op_challenge, create_challenge()],
			[Txn.application_args[0] == op_accept, accept_challenge()],
			[Txn.application_args[0] == op_reveal, reveal()]
		),
		Reject()
    )

	program = Cond(
		[Txn.application_id() == Int(0), init],
		# [Txn.on_completion() == OnComplete.DeleteApplication, delete],
		# [Txn.on_completion() == OnComplete.UpdateApplication, update],
		[Txn.on_completion() == OnComplete.OptIn, opt_in],
		# [Txn.on_completion() == OnComplete.CloseOut, close_out],
		[Txn.on_completion() == OnComplete.NoOp, no_op]
	)
	return program


def clear_state_program():
    program = Return(Int(1))
    return program


if __name__ == "__main__":
	compiled_approval = compileTeal(approval_program(), Mode.Application, version=6)
	compiled_clear = compileTeal(clear_state_program(), Mode.Application, version=6)

with open("../build/approval.teal", "w") as teal:
	teal.write(compiled_approval)
	teal.close()

with open("../build/clear.teal", "w") as teal:
	teal.write(compiled_clear)
	teal.close()

