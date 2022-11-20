from pyteal import *
from pyteal.ast.bytes import Bytes

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

	@Subroutine(TealType.uint64)
	def is_empty(account: Expr):
		return Return(
            And(
                App.localGet(account, local_opponent) == Bytes(""),
                App.localGet(account, local_wager) == Int(0),
                App.localGet(account, local_commitment) == Bytes(""),
                App.localGet(account, local_reveal) == Bytes(""),
            )
        )

	@Subroutine(TealType.uint64)
	def is_valid_play(play: Expr):
		first_character = ScratchVar(TealType.bytes)
		return Seq(
		first_character.store(Substring(play, Int(0), Int(1))),
		Return(
			Or(
				first_character.load() == Bytes("r"),
				first_character.load() == Bytes("p"),
				first_character.load() == Bytes("s")
			)
		)
	)


	@Subroutine(TealType.none)
	def create_challenge():
		return Seq(

            Assert(
				And(
					*[
                		Gtxn[i].rekey_to() == Global.zero_address()
                		for i in range(2)
            		]
				),
                And(

					Global.group_size() == Int(2),
            		Txn.group_index() == Int(0),

                    # second transaction is wager payment
                    Gtxn[1].type_enum() == TxnType.Payment,
                    Gtxn[1].receiver() == Global.current_application_address(),
                    Gtxn[1].close_remainder_to() == Global.zero_address(),
                    # second account has opted-in
                    App.optedIn(Int(1), Int(0)),
                    is_empty(Int(0)),
                    is_empty(Int(1)),
                    # commitment
                    Txn.application_args.length() == Int(2),
                )
            ),
            App.localPut(Txn.sender(), local_opponent, Txn.accounts[1]),
            App.localPut(Txn.sender(), local_wager, Gtxn[1].amount()),
            App.localPut(
                Txn.sender(),
                local_commitment,
                Txn.application_args[1],
            ),
            Approve(),
        )


	@Subroutine(TealType.none)
	def accept_challenge():
		return Seq(

            Assert(
				And(
					*[
                		Gtxn[i].rekey_to() == Global.zero_address()
                		for i in range(2)
            		]
				),
				And(

					Global.group_size() == Int(2),
            		Txn.group_index() == Int(0),

                    # second transaction is wager payment
                    Gtxn[1].type_enum() == TxnType.Payment,
                    Gtxn[1].receiver() == Global.current_application_address(),
                    Gtxn[1].close_remainder_to() == Global.zero_address(),

					# One of the ways to check if there is a challenge and be sure of the amount.
					Gtxn[1].amount() == App.localGet(Txn.accounts[1], local_wager),

                    # second account has opted-in
                    App.optedIn(Int(1), Int(0)),
					App.localGet(Txn.accounts[1], local_opponent) == Txn.sender(),

                    # reveal
                    Txn.application_args.length() == Int(2),
					is_valid_play(Txn.application_args[1]),
                ),
			),
			App.localPut(Txn.sender(), local_opponent, Txn.accounts[1]),
            App.localPut(Txn.sender(), local_wager, Gtxn[1].amount()),
            App.localPut(
                Txn.sender(),
                local_reveal,
                Txn.application_args[1],
            ),
            Approve(),

		)

	@Subroutine(TealType.uint64)
	def play_value(p: Expr):
		first_letter = ScratchVar()
		return Seq(
            first_letter.store(Substring(p, Int(0), Int(1))),
            Return(
                Cond(
                    [first_letter.load() == Bytes("r"), Int(0)],
                    [first_letter.load() == Bytes("p"), Int(1)],
                    [first_letter.load() == Bytes("s"), Int(2)],
                )
            ),
        )

	@Subroutine(TealType.uint64)
	def winner_account_index(play: Expr, opponent_play: Expr):
		return Return(
            Cond(
                [play == opponent_play, Int(2)],  # tie
                [(play + Int(1)) % Int(3) == opponent_play, Int(1)],  # opponent wins
                [
                    (opponent_play + Int(1)) % Int(3) == play,
                    Int(0),
                ],  # current account win
            )
        )


	@Subroutine(TealType.none)
	def send_reward(account_index: Expr, amount: Expr):
		return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.receiver: Txn.accounts[account_index],
                    TxnField.amount: amount,
                    TxnField.fee: Int(0),  # use fee pooling
                }
            ),
            InnerTxnBuilder.Submit(),
        )


	@Subroutine(TealType.none)
	def reveal():
		winner = ScratchVar()
		wager = ScratchVar()
		return Seq(
            Assert(
				And(
					*[
                		Gtxn[i].rekey_to() == Global.zero_address()
                		for i in range(1)
            		]
				),
				And(

					Global.group_size() == Int(1),
            		Txn.group_index() == Int(0),

                    # verify game data matches
                    App.localGet(Int(0), local_opponent) == Txn.accounts[1],
                    App.localGet(Int(1), local_opponent) == Txn.sender(),
                    App.localGet(Int(0), local_wager)
                    == App.localGet(Int(1), local_wager),
                    # this account has commitment
                    App.localGet(Int(0), local_commitment) != Bytes(""),
                    # opponent account has a reveal
                    App.localGet(Int(1), local_reveal) != Bytes(""),
                    # require reveal argument
                    Txn.application_args.length() == Int(2),
                    # validate reveal
                    # Sha256(Txn.application_args[1])
                    # == App.localGet(Int(0), local_commitment),
                )
            ),
            wager.store(App.localGet(Int(0), local_wager)),
            winner.store(
                winner_account_index(
                    play_value(Txn.application_args[1]),
                    play_value(App.localGet(Int(1), local_reveal)),
                )
            ),
            If(winner.load() == Int(2))
            .Then(
                # tie: refund wager to each party
                Seq(
                    # require first transaction fee to cover:
                    # - own transaction fee
                    # - each reward transaction fee
                    Assert(Txn.fee() >= Global.min_txn_fee() * Int(3)),
                    send_reward(Int(0), wager.load()),
                    send_reward(Int(1), wager.load()),
                )
            )
            .Else(
                # send double wager to winner
                Seq(
                    # require first transaction fee to cover:
                    # - own transaction fee
                    # - reward transaction fee
                    Assert(Txn.fee() >= Global.min_txn_fee() * Int(2)),
                    send_reward(winner.load(), wager.load() * Int(2)),
                )
            ),
            reset(Int(0)),
            reset(Int(1)),
            Approve(),
        )

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

