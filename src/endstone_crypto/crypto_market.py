# src/endstone_crypto/crypto_market.py
import json
import math
import random
import re
from collections import deque, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple, Callable

from endstone.plugin import Plugin
from endstone.command import Command, CommandSender
from endstone.event import event_handler, BlockBreakEvent, PlayerJoinEvent
from endstone import Player  # Endstone 0.11.*
from endstone.form import ActionForm, ModalForm, TextInput, Dropdown, Label
from endstone.scoreboard import Criteria

# ──────────────────────────────────────────────────────────────────────────────
# Config dataclasses
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CoinSpec:
    symbol: str
    name: str
    start_price: float
    min_price: float
    max_price: float
    volatility: float         # daily-ish pct sigma (scaled per tick)
    mining_weight: float      # relative drop chance weight
    momentum: float           # 0..1 blend into trend
    fee_bps: int              # trade fee (basis points)

@dataclass
class Config:
    enabled: bool
    tick_seconds: int
    chart_points: int
    broadcast_every: int       # number of price ticks (not server ticks)
    award_min_depth: int       # Y ≤ this doubles award chance
    base_drop_chance: float    # baseline probability per eligible break
    ores: Dict[str, float]     # block id -> drop multiplier
    coins: List[CoinSpec]

# ──────────────────────────────────────────────────────────────────────────────
# Plugin (command-only)
# ──────────────────────────────────────────────────────────────────────────────

class CryptoMarket(Plugin):
    
    version = "3.0.8"          # Full GUI + scoreboard Money integration + player names with spaces support
    api_version = "0.11"
    description = "Crypto simulation with GUI: prices, mining drops, bank & P2P trading with scoreboard Money."
    prefix = "Crypto"

    # IMPORTANT: capture whole tail so subcommands work: /crypto [tail: message]
    commands = {
        "crypto": {
            "description": "Crypto commands (/crypto help).",
            "usages": ["/crypto [tail: message]"],
            "permissions": ["endstone_crypto.command.crypto"],
            "aliases": ["market", "coinswap"],
        }
    }
    permissions = {
        "endstone_crypto.command.crypto": {
            "description": "Allow users to use /crypto.",
            "default": "true",
        },
        "endstone_crypto.admin": {
            "description": "Admin permission for all crypto controls.",
            "default": "op",
        },
    }

    # ── lifecycle ────────────────────────────────────────────────────────────
    def on_enable(self) -> None:
        self.logger.info(f"[EndstoneCrypto] Enabling v{self.version} (api {self.api_version})")

        self._init_files()
        self._load_config()
        self._load_state()
        self._load_offers()
        self._load_players_index()

        self.register_events(self)

        # Schedule price loop: Endstone uses ticks (20 ticks ~= 1s).
        if self.cfg.enabled:
            ticks = max(1, int(self.cfg.tick_seconds * 20))
            self.server.scheduler.run_task(self, self._safe_price_tick, delay=ticks, period=ticks)
            self.logger.info(f"[EndstoneCrypto] Price loop scheduled every {self.cfg.tick_seconds}s.")

        self.logger.info("[EndstoneCrypto] /crypto command ready.")

    def _safe_price_tick(self):
        try:
            self._price_tick()
        except Exception as ex:
            self.logger.error(f"Price tick failed: {ex}")

    # Helper to parse command arguments with support for quoted strings
    def _parse_args(self, tail: str) -> List[str]:
        """Parse command arguments, supporting quoted strings for player names with spaces.

        Examples:
            'send "Player Name" NINJ 5' -> ['send', 'Player Name', 'NINJ', '5']
            'send PlayerName NINJ 5' -> ['send', 'PlayerName', 'NINJ', '5']
            'offer "Player Name" NINJ 5 100' -> ['offer', 'Player Name', 'NINJ', '5', '100']
        """
        parts = []
        current = []
        in_quotes = False
        i = 0

        while i < len(tail):
            char = tail[i]

            if char == '"':
                in_quotes = not in_quotes
                i += 1
                continue

            if char == ' ' and not in_quotes:
                if current:
                    parts.append(''.join(current))
                    current = []
                i += 1
                continue

            current.append(char)
            i += 1

        if current:
            parts.append(''.join(current))

        return parts

    # Endstone 0.11 handler signature: (sender, command, args)
    def on_command(self, sender: CommandSender, command: Command, args: List[str]) -> bool:
        if command.name != "crypto":
            return False
        if not isinstance(sender, Player):
            sender.send_message("[Crypto] Use this in-game.")
            return True

        # We declared usages: "/crypto [tail: message]".
        # Endstone will pass either [] or [tail_string].
        tail = (args[0] if (args and isinstance(args[0], str)) else "").strip()
        parts: List[str] = self._parse_args(tail) if tail else []

        # No args -> open GUI
        if not parts:
            self._show_main_menu(sender)
            return True

        sub = parts[0].lower()

        # help command
        if sub in ("help", "?"):
            self._send_help(sender)
            return True

        # ── admin suite ──────────────────────────────────────────────────────
        if sub == "admin":
            return self._cmd_admin(sender, parts[1:])

        # ── player suite ─────────────────────────────────────────────────────
        if sub in ("symbols", "coins"):
            self._cmd_coins(sender)
            return True

        if sub == "price" and len(parts) >= 2:
            self._cmd_price(sender, parts[1])
            return True

        if sub == "chart" and len(parts) >= 2:
            self._cmd_chart(sender, parts[1])
            return True

        if sub in ("holdings", "balance", "bal"):
            self._cmd_holdings(sender)
            return True

        if sub == "send" and len(parts) >= 4:
            self._cmd_send(sender, parts[1], parts[2], parts[3])
            return True

        if sub == "offer" and len(parts) >= 5:
            self._cmd_offer(sender, parts[1], parts[2], parts[3], parts[4])
            return True

        if sub == "offers":
            which = parts[1].lower() if len(parts) >= 2 else "mine"
            self._cmd_offers(sender, which)
            return True

        if sub == "accept" and len(parts) >= 2:
            self._cmd_accept(sender, parts[1])
            return True

        if sub == "cancel" and len(parts) >= 2:
            self._cmd_cancel(sender, parts[1])
            return True

        if sub == "market" and len(parts) >= 4:
            side = parts[1].lower()
            sym = parts[2]
            qty = parts[3]
            if side == "buy":
                self._cmd_market_buy(sender, sym, qty)
                return True
            if side == "sell":
                self._cmd_market_sell(sender, sym, qty)
                return True

        sender.send_message("§c[Crypto] Unknown usage. Try §e/crypto help")
        return True

    # ── events ───────────────────────────────────────────────────────────────
    @event_handler
    def on_player_join(self, e: PlayerJoinEvent):
        try:
            self._players_index[e.player.unique_id.hex] = e.player.name
            self._save_players_index()
        except Exception:
            pass
        creds = self._get_credits(e.player)
        try:
            e.player.send_toast("Crypto", f"Welcome! Credits: {creds} • /crypto help")
        except Exception:
            e.player.send_message(f"§a[Crypto] Welcome! Credits: {creds} • /crypto help")

    @event_handler
    def on_block_break(self, e: BlockBreakEvent):
        if not self.cfg.enabled:
            return
        p: Player = e.player
        block = e.block
        block_id = getattr(block, "type", None) or getattr(block, "id", "")
        y = getattr(block, "y", 64)

        ore_mult = self.cfg.ores.get(block_id, 0.0)
        if ore_mult <= 0:
            return

        chance = self.cfg.base_drop_chance * ore_mult
        if y <= self.cfg.award_min_depth:
            chance *= 2.0

        if random.random() <= chance:
            symbol = self._pick_mining_coin()
            price = self.state["prices"][symbol]
            depth_boost = (self.cfg.award_min_depth - min(self.cfg.award_min_depth, y)) * 0.01
            qty = max(0.0001, round(random.uniform(0.001, 0.01) * (1.0 + depth_boost), 4))
            self._add_holdings(p, symbol, qty)
            p.send_message(f"§a[Crypto] You mined {qty:.4f} {symbol} (≈ ${qty*price:.2f}).")
            self._save_holdings_for(p)

    # ── GUI methods ──────────────────────────────────────────────────────────
    def _show_main_menu(self, p: Player):
        """Main crypto market menu"""
        money = self._get_money(p)
        creds = self._get_credits(p)

        form = ActionForm(
            title="§l§6Crypto Market",
            content=f"§7Welcome to the Crypto Market!\n§eMoney: §a${money:,}\n§bInternal Credits: §a{creds:,}\n\n§7Choose an option:"
        )

        form.add_button("§l§2Buy Crypto", icon="textures/ui/icon_recipe_item", on_click=lambda pl: self._show_buy_menu(pl))
        form.add_button("§l§cSell Crypto", icon="textures/ui/icon_recipe_equipment", on_click=lambda pl: self._show_sell_menu(pl))
        form.add_button("§l§bMy Portfolio", icon="textures/ui/icon_book_writable", on_click=lambda pl: self._show_portfolio(pl))
        form.add_button("§l§eMarket Prices", icon="textures/ui/icon_deals", on_click=lambda pl: self._show_market_prices(pl))
        form.add_button("§l§6P2P Trading", icon="textures/ui/icon_multiplayer", on_click=lambda pl: self._show_p2p_menu(pl))
        form.add_button("§l§3Deposit Money", icon="textures/ui/icon_import", on_click=lambda pl: self._show_deposit_form(pl))
        form.add_button("§l§dWithdraw Money", icon="textures/ui/icon_export", on_click=lambda pl: self._show_withdraw_form(pl))

        p.send_form(form)

    def _show_buy_menu(self, p: Player):
        """Show coin selection for buying"""
        money = self._get_money(p)

        form = ActionForm(
            title="§l§2Buy Crypto",
            content=f"§7Select a coin to buy\n§eMoney Available: §a${money:,}"
        )

        for coin in self.cfg.coins:
            price = self.state["prices"][coin.symbol]
            chart = self._mini_chart(coin.symbol, tall=False)
            form.add_button(
                f"§l{coin.symbol}\n§r§7${price:,.2f}",
                on_click=lambda pl, sym=coin.symbol: self._show_buy_form(pl, sym)
            )

        form.add_button("§l§8« Back", on_click=lambda pl: self._show_main_menu(pl))
        p.send_form(form)

    def _show_sell_menu(self, p: Player):
        """Show coin selection for selling"""
        inv = self._holdings.get(p.unique_id.hex, {})
        coins = [(s, q) for s, q in inv.items() if s != "_credits" and q > 0]

        form = ActionForm(
            title="§l§cSell Crypto",
            content="§7Select a coin to sell"
        )

        if not coins:
            form.content = "§cYou don't own any crypto yet!\n§7Mine ores or buy some first."
            form.add_button("§l§8« Back", on_click=lambda pl: self._show_main_menu(pl))
        else:
            for sym, qty in sorted(coins):
                price = self.state["prices"].get(sym, 0.0)
                value = qty * price
                form.add_button(
                    f"§l{sym}\n§r§7{qty:.4f} (≈${value:,.2f})",
                    on_click=lambda pl, s=sym: self._show_sell_form(pl, s)
                )
            form.add_button("§l§8« Back", on_click=lambda pl: self._show_main_menu(pl))

        p.send_form(form)

    def _show_buy_form(self, p: Player, symbol: str):
        """Form to buy a specific coin"""
        price = self.state["prices"][symbol]
        spec = self._coin_spec(symbol)
        fee = spec.fee_bps / 10000.0
        money = self._get_money(p)

        form = ModalForm(
            title=f"§l§2Buy {symbol}",
            submit_button="§l§aBuy Now"
        )

        chart = self._mini_chart(symbol, tall=True)
        form.add_control(Label(f"§7{spec.name}\n{chart}\n§7Current Price: §e${price:,.2f}\n§7Fee: §c{fee*100:.2f}%\n§7Your Money: §a${money:,}"))
        form.add_control(TextInput(label="§eQuantity to Buy", placeholder="0.0001"))

        def on_buy(pl: Player, data: str):
            import json as j
            try:
                vals = j.loads(data)
                qty_str = vals[1].strip()
                if not qty_str:
                    pl.send_message("§c[Crypto] Please enter a quantity.")
                    return
                qty = float(qty_str)
                if qty <= 0:
                    pl.send_message("§c[Crypto] Quantity must be > 0.")
                    return

                total = math.ceil(price * qty * (1.0 + fee))
                current_money = self._get_money(pl)

                if current_money < total:
                    pl.send_message(f"§c[Crypto] Need ${total:,}; you have ${current_money:,}.")
                    return

                self._set_money(pl, current_money - total)
                self._add_holdings(pl, symbol, +qty)
                self._save_holdings_for(pl)
                pl.send_message(f"§a[Crypto] Bought {qty:.4f} {symbol} for ${total:,} (incl. fees).")
            except Exception as e:
                pl.send_message(f"§c[Crypto] Invalid input: {e}")

        form.on_submit = on_buy
        form.on_close = lambda pl: self._show_buy_menu(pl)
        p.send_form(form)

    def _show_sell_form(self, p: Player, symbol: str):
        """Form to sell a specific coin"""
        price = self.state["prices"][symbol]
        spec = self._coin_spec(symbol)
        fee = spec.fee_bps / 10000.0
        holdings = self._get_holdings(p, symbol)

        form = ModalForm(
            title=f"§l§cSell {symbol}",
            submit_button="§l§cSell Now"
        )

        chart = self._mini_chart(symbol, tall=True)
        form.add_control(Label(f"§7{spec.name}\n{chart}\n§7Current Price: §e${price:,.2f}\n§7Fee: §c{fee*100:.2f}%\n§7You Own: §a{holdings:.4f} {symbol}"))
        form.add_control(TextInput(label="§eQuantity to Sell", placeholder="0.0001"))

        def on_sell(pl: Player, data: str):
            import json as j
            try:
                vals = j.loads(data)
                qty_str = vals[1].strip()
                if not qty_str:
                    pl.send_message("§c[Crypto] Please enter a quantity.")
                    return
                qty = float(qty_str)
                if qty <= 0:
                    pl.send_message("§c[Crypto] Quantity must be > 0.")
                    return

                current_holdings = self._get_holdings(pl, symbol)
                if current_holdings < qty:
                    pl.send_message(f"§c[Crypto] You only have {current_holdings:.4f} {symbol}.")
                    return

                proceeds = math.floor(price * qty * (1.0 - fee))
                current_money = self._get_money(pl)

                self._set_money(pl, current_money + proceeds)
                self._add_holdings(pl, symbol, -qty)
                self._save_holdings_for(pl)
                pl.send_message(f"§a[Crypto] Sold {qty:.4f} {symbol} for ${proceeds:,} (after fees).")
            except Exception as e:
                pl.send_message(f"§c[Crypto] Invalid input: {e}")

        form.on_submit = on_sell
        form.on_close = lambda pl: self._show_sell_menu(pl)
        p.send_form(form)

    def _show_portfolio(self, p: Player):
        """Show player's portfolio"""
        money = self._get_money(p)
        creds = self._get_credits(p)
        inv = self._holdings.get(p.unique_id.hex, {})
        coins = [(s, q) for s, q in inv.items() if s != "_credits" and q > 0]

        total_value = sum(q * self.state["prices"].get(s, 0.0) for s, q in coins)

        content = f"§eMoney: §a${money:,}\n§bInternal Credits: §a{creds:,}\n§6Total Crypto Value: §a${total_value:,.2f}\n\n"

        if coins:
            content += "§b§lYour Holdings:\n"
            for sym, qty in sorted(coins):
                price = self.state["prices"].get(sym, 0.0)
                value = qty * price
                content += f"§f{sym}: §7{qty:.4f} §8(≈${value:,.2f})\n"
        else:
            content += "§7No crypto holdings yet.\n§7Mine ores or buy some!"

        form = ActionForm(
            title="§l§bMy Portfolio",
            content=content
        )

        form.add_button("§l§8« Back", on_click=lambda pl: self._show_main_menu(pl))
        p.send_form(form)

    def _show_market_prices(self, p: Player):
        """Show all market prices"""
        content = "§b§lMarket Prices\n\n"

        for coin in self.cfg.coins:
            price = self.state["prices"][coin.symbol]
            content += f"§f{coin.symbol} §7({coin.name}): §e${price:,.2f}\n"

        form = ActionForm(
            title="§l§eMarket Prices",
            content=content
        )

        for coin in self.cfg.coins:
            form.add_button(
                f"§l{coin.symbol} Chart",
                on_click=lambda pl, sym=coin.symbol: self._show_chart(pl, sym)
            )

        form.add_button("§l§8« Back", on_click=lambda pl: self._show_main_menu(pl))
        p.send_form(form)

    def _show_chart(self, p: Player, symbol: str):
        """Show chart for a specific coin"""
        spec = self._coin_spec(symbol)
        price = self.state["prices"][symbol]
        chart = self._mini_chart(symbol, tall=True)

        form = ActionForm(
            title=f"§l§3{symbol} Chart",
            content=f"§7{spec.name}\n\n{chart}\n\n§7Current Price: §e${price:,.2f}"
        )

        form.add_button("§l§2Buy", on_click=lambda pl: self._show_buy_form(pl, symbol))
        form.add_button("§l§cSell", on_click=lambda pl: self._show_sell_form(pl, symbol))
        form.add_button("§l§8« Back", on_click=lambda pl: self._show_market_prices(pl))
        p.send_form(form)

    def _show_p2p_menu(self, p: Player):
        """P2P trading menu"""
        form = ActionForm(
            title="§l§6P2P Trading",
            content="§7Trade directly with other players"
        )

        form.add_button("§l§aCreate Offer", on_click=lambda pl: self._show_create_offer_form(pl))
        form.add_button("§l§bView All Offers", on_click=lambda pl: self._show_all_offers(pl))
        form.add_button("§l§eMy Offers", on_click=lambda pl: self._show_my_offers(pl))
        form.add_button("§l§8« Back", on_click=lambda pl: self._show_main_menu(pl))

        p.send_form(form)

    def _show_create_offer_form(self, p: Player):
        """Form to create a P2P offer"""
        inv = self._holdings.get(p.unique_id.hex, {})
        coins = [(s, q) for s, q in inv.items() if s != "_credits" and q > 0]

        if not coins:
            empty_form = ActionForm(
                title="§l§aCreate Offer",
                content="§cYou don't own any crypto to sell!"
            )
            empty_form.add_button("§l§8« Back", on_click=lambda pl: self._show_p2p_menu(pl))
            p.send_form(empty_form)
            return

        form = ModalForm(
            title="§l§aCreate P2P Offer",
            submit_button="§l§aCreate Offer"
        )

        coin_options = [f"{s} ({q:.4f} available)" for s, q in sorted(coins)]
        form.add_control(Label("§7Create an offer to sell crypto to another player"))
        form.add_control(Dropdown(label="§eCoin to Sell", options=coin_options))
        form.add_control(TextInput(label="§eQuantity", placeholder="0.0001"))
        form.add_control(TextInput(label="§ePrice Per Coin ($)", placeholder="100.00"))
        form.add_control(TextInput(label="§eTarget Player (optional)", placeholder="PlayerName"))

        def on_create(pl: Player, data: str):
            import json as j
            try:
                vals = j.loads(data)
                coin_idx = vals[1]
                qty_str = vals[2].strip()
                price_str = vals[3].strip()
                target_str = vals[4].strip()

                symbol = sorted(coins)[coin_idx][0]
                qty = float(qty_str)
                price_per = float(price_str)

                if qty <= 0 or price_per <= 0:
                    pl.send_message("§c[Crypto] Quantity and price must be > 0.")
                    return

                # Use existing offer command logic
                parts = ["offer"]
                if target_str:
                    parts.append(target_str)
                else:
                    parts.append("*")
                parts.extend([symbol, str(qty), str(price_per)])

                self._cmd_offer(pl, parts[1], parts[2], parts[3], parts[4])
            except Exception as e:
                pl.send_message(f"§c[Crypto] Invalid input: {e}")

        form.on_submit = on_create
        form.on_close = lambda pl: self._show_p2p_menu(pl)
        p.send_form(form)

    def _show_all_offers(self, p: Player):
        """Show all available P2P offers"""
        self._cmd_offers(p, "all")
        # Return to menu after showing offers
        self.server.scheduler.run_task(self, lambda: self._show_p2p_menu(p), delay=1)

    def _show_my_offers(self, p: Player):
        """Show player's own offers"""
        self._cmd_offers(p, "mine")
        # Return to menu after showing offers
        self.server.scheduler.run_task(self, lambda: self._show_p2p_menu(p), delay=1)

    def _show_deposit_form(self, p: Player):
        """Form to deposit internal credits to Money scoreboard"""
        creds = self._get_credits(p)

        form = ModalForm(
            title="§l§3Deposit to Money",
            submit_button="§l§aDeposit"
        )

        form.add_control(Label(f"§7Convert internal credits to Money\n§bInternal Credits: §a{creds:,}"))
        form.add_control(TextInput(label="§eAmount to Deposit", placeholder="1000"))

        def on_deposit(pl: Player, data: str):
            import json as j
            try:
                vals = j.loads(data)
                amt_str = vals[1].strip()
                if not amt_str:
                    pl.send_message("§c[Crypto] Please enter an amount.")
                    return
                amt = int(amt_str)
                if amt <= 0:
                    pl.send_message("§c[Crypto] Amount must be > 0.")
                    return

                current_creds = self._get_credits(pl)
                if current_creds < amt:
                    pl.send_message(f"§c[Crypto] You only have {current_creds:,} credits.")
                    return

                self._add_credits(pl, -amt)
                self._add_money(pl, amt)
                pl.send_message(f"§a[Crypto] Deposited {amt:,} credits to Money.")
            except Exception as e:
                pl.send_message(f"§c[Crypto] Invalid input: {e}")

        form.on_submit = on_deposit
        form.on_close = lambda pl: self._show_main_menu(pl)
        p.send_form(form)

    def _show_withdraw_form(self, p: Player):
        """Form to withdraw Money to internal credits"""
        money = self._get_money(p)

        form = ModalForm(
            title="§l§dWithdraw from Money",
            submit_button="§l§cWithdraw"
        )

        form.add_control(Label(f"§7Convert Money to internal credits\n§eMoney: §a${money:,}"))
        form.add_control(TextInput(label="§eAmount to Withdraw", placeholder="1000"))

        def on_withdraw(pl: Player, data: str):
            import json as j
            try:
                vals = j.loads(data)
                amt_str = vals[1].strip()
                if not amt_str:
                    pl.send_message("§c[Crypto] Please enter an amount.")
                    return
                amt = int(amt_str)
                if amt <= 0:
                    pl.send_message("§c[Crypto] Amount must be > 0.")
                    return

                current_money = self._get_money(pl)
                if current_money < amt:
                    pl.send_message(f"§c[Crypto] You only have ${current_money:,}.")
                    return

                self._set_money(pl, current_money - amt)
                self._add_credits(pl, amt)
                pl.send_message(f"§a[Crypto] Withdrew ${amt:,} from Money to credits.")
            except Exception as e:
                pl.send_message(f"§c[Crypto] Invalid input: {e}")

        form.on_submit = on_withdraw
        form.on_close = lambda pl: self._show_main_menu(pl)
        p.send_form(form)

    # ── player commands ──────────────────────────────────────────────────────
    def _send_help(self, p: Player):
        lines = [
            "§b§lCrypto Commands",
            "§7Prices move automatically; mine ores to find coins.",
            "§6/crypto§7 — open GUI (recommended!)",
            "§6/crypto symbols§7 — list all symbols",
            "§6/crypto coins§7 — list coins & prices",
            "§6/crypto price <sym>§7 — show current price",
            "§6/crypto chart <sym>§7 — ASCII chart",
            "§6/crypto holdings§7 — show your coins & credits",
            "§6/crypto send <player> <sym> <qty>§7 — transfer coin",
            "§6/crypto offer <player> <sym> <qty> <price_per>§7 — sell to a player",
            "§6/crypto offers [mine|all]§7 — list offers",
            "§6/crypto accept <id>§7 / §6/crypto cancel <id>",
            "§6/crypto market buy <sym> <qty>§7 — buy from bank",
            "§6/crypto market sell <sym> <qty>§7 — sell to bank",
            "§8Admins: /crypto admin help",
        ]
        for s in lines:
            p.send_message(s)

    def _cmd_coins(self, p: Player):
        p.send_message("§b§lCoins & Prices")
        for sym in self._coin_symbols():
            price = self.state["prices"][sym]
            p.send_message(f"§b{sym}§7 — ${price:.2f}")

    def _cmd_price(self, p: Player, symbol: str):
        ok, sym, err = self._resolve_symbol(symbol)
        if not ok:
            p.send_message(err); return
        p.send_message(f"§b{sym}§7 — ${self.state['prices'][sym]:.2f}")

    def _cmd_chart(self, p: Player, symbol: str):
        ok, sym, err = self._resolve_symbol(symbol)
        if not ok:
            p.send_message(err); return
        p.send_message(self._mini_chart(sym, tall=True))
        p.send_message(f"§7Now: §l${self.state['prices'][sym]:.2f}")

    def _cmd_holdings(self, p: Player):
        creds = self._get_credits(p)
        p.send_message(f"§bCredits: §l{creds}")
        inv = self._holdings.get(p.unique_id.hex, {})
        coins = [(s, q) for s, q in inv.items() if s != "_credits" and q > 0]
        if not coins:
            p.send_message("§7You have no coins yet. Mine ores or buy via /crypto market buy …")
            return
        p.send_message("§b§lYour Coins")
        for sym, qty in sorted(coins):
            price = self.state["prices"].get(sym, 0.0)
            p.send_message(f"§f{sym} §7x {qty:.4f}  §8(≈ ${qty*price:.2f})")

    def _cmd_send(self, p: Player, target_name: str, symbol: str, qty_s: str):
        target = self.server.get_player(target_name)
        if target is None:
            p.send_message("§c[Crypto] Player not found (online required)."); return
        ok, sym, err = self._resolve_symbol(symbol)
        if not ok:
            p.send_message(err); return
        try:
            qty = float(qty_s)
        except Exception:
            p.send_message("§c[Crypto] Invalid quantity."); return
        if qty <= 0:
            p.send_message("§c[Crypto] Quantity must be > 0."); return
        if self._get_holdings(p, sym) < qty:
            p.send_message(f"§c[Crypto] You only have {self._get_holdings(p, sym):.4f} {sym}."); return
        self._add_holdings(p, sym, -qty)
        self._add_holdings(target, sym, +qty)
        self._save_holdings_for(p)
        self._save_holdings_for(target)
        p.send_message(f"§a[Crypto] Sent {qty:.4f} {sym} to {target.name}.")
        target.send_message(f"§a[Crypto] {p.name} sent you {qty:.4f} {sym}.")

    def _cmd_offer(self, p: Player, target_name: str, symbol: str, qty_s: str, price_s: str):
        target = self.server.get_player(target_name)
        if target is None:
            p.send_message("§c[Crypto] Target player not found (online required)."); return
        ok, sym, err = self._resolve_symbol(symbol)
        if not ok:
            p.send_message(err); return
        try:
            qty = float(qty_s)
            price_per = float(price_s)
        except Exception:
            p.send_message("§c[Crypto] Invalid qty/price."); return
        if qty <= 0 or price_per <= 0:
            p.send_message("§c[Crypto] Quantity and price must be > 0."); return
        if self._get_holdings(p, sym) < qty:
            p.send_message("§c[Crypto] You do not have enough coins to create this offer."); return

        oid = str(self._next_offer_id); self._next_offer_id += 1
        self._offers[oid] = {
            "id": oid,
            "seller": p.unique_id.hex,
            "seller_name": p.name,
            "buyer": target.unique_id.hex,
            "buyer_name": target.name,
            "symbol": sym,
            "qty": float(f"{qty:.4f}"),
            "price_per": float(f"{price_per:.4f}"),
            "status": "open",
            "created_tick": int(self.state.get("tick", 0)),
        }
        self._save_offers()
        p.send_message(f"§a[Crypto] Offer #{oid} created for {target.name}: {qty:.4f} {sym} @ {price_per:.4f} credits each.")
        target.send_message(f"§e[Crypto] {p.name} offered you #{oid}: {qty:.4f} {sym} @ {price_per:.4f}/ea. Use §6/crypto accept {oid}§e to buy.")

    def _cmd_offers(self, p: Player, which: str):
        which = which.lower()
        p.send_message("§b§lOffers")
        shown = 0
        for oid, o in self._offers.items():
            if o["status"] != "open":
                continue
            if which == "mine" and o["buyer"] != p.unique_id.hex and o["seller"] != p.unique_id.hex:
                continue
            p.send_message(f"§7#{oid} §f{ o['seller_name'] } §8→§f { o['buyer_name'] } §7— {o['qty']:.4f} {o['symbol']} @ {o['price_per']:.4f}/ea")
            shown += 1
        if shown == 0:
            p.send_message("§7(no open offers)")

    def _cmd_accept(self, p: Player, offer_id: str):
        o = self._offers.get(offer_id)
        if not o or o["status"] != "open":
            p.send_message("§c[Crypto] Offer not found or already closed."); return
        if o["buyer"] != p.unique_id.hex:
            p.send_message("§c[Crypto] This offer is not addressed to you."); return
        seller_uuid = o["seller"]; sym = o["symbol"]
        qty = float(o["qty"]); price_per = float(o["price_per"])
        total = math.ceil(qty * price_per)

        buyer_creds = self._get_credits(p)
        if buyer_creds < total:
            p.send_message(f"§c[Crypto] You need {total} credits; you have {buyer_creds}."); return

        seller_player = self._find_player_by_uuid_hex(seller_uuid)
        seller_has = self._get_holdings_by_uuid(seller_uuid, sym)
        if seller_has < qty:
            p.send_message("§c[Crypto] Seller no longer has enough coins. Offer cancelled.")
            o["status"] = "cancelled"; self._save_offers(); return

        self._add_credits(p, -total)
        if seller_player:
            self._add_credits(seller_player, +total)
        else:
            self._add_credits_by_uuid(seller_uuid, +total)

        self._add_holdings_by_uuid(seller_uuid, sym, -qty)
        self._add_holdings(p, sym, +qty)

        o["status"] = "filled"; self._save_offers()
        self._save_holdings_for(p)
        if seller_player:
            self._save_holdings_for(seller_player)

        p.send_message(f"§a[Crypto] Filled offer #{offer_id}: bought {qty:.4f} {sym} for {total} credits.")
        if seller_player:
            seller_player.send_message(f"§a[Crypto] Your offer #{offer_id} was accepted: +{total} credits, -{qty:.4f} {sym}.")

    def _cmd_cancel(self, p: Player, offer_id: str):
        o = self._offers.get(offer_id)
        if not o or o["status"] != "open":
            p.send_message("§c[Crypto] Offer not found or already closed."); return
        if o["seller"] != p.unique_id.hex and o["buyer"] != p.unique_id.hex and not p.has_permission("endstone_crypto.admin"):
            p.send_message("§c[Crypto] You cannot cancel this offer."); return
        o["status"] = "cancelled"; self._save_offers()
        p.send_message(f"§e[Crypto] Offer #{offer_id} cancelled.")

    def _cmd_market_buy(self, p: Player, symbol: str, qty_s: str):
        ok, sym, err = self._resolve_symbol(symbol)
        if not ok:
            p.send_message(err); return
        try:
            qty = float(qty_s)
        except Exception:
            p.send_message("§c[Crypto] Invalid quantity."); return
        if qty <= 0:
            p.send_message("§c[Crypto] Quantity must be > 0."); return
        price = self.state["prices"][sym]
        fee = self._coin_spec(sym).fee_bps / 10000.0
        total = math.ceil(price * qty * (1.0 + fee))
        if self._get_credits(p) < total:
            p.send_message(f"§c[Crypto] Need {total} credits; you have {self._get_credits(p)}."); return
        self._add_credits(p, -total)
        self._add_holdings(p, sym, +qty)
        self._save_holdings_for(p)
        p.send_message(f"§a[Crypto] Bought {qty:.4f} {sym} for {total} credits (incl. fees).")

    def _cmd_market_sell(self, p: Player, symbol: str, qty_s: str):
        ok, sym, err = self._resolve_symbol(symbol)
        if not ok:
            p.send_message(err); return
        try:
            qty = float(qty_s)
        except Exception:
            p.send_message("§c[Crypto] Invalid quantity."); return
        if qty <= 0:
            p.send_message("§c[Crypto] Quantity must be > 0."); return
        if self._get_holdings(p, sym) < qty:
            p.send_message(f"§c[Crypto] You only have {self._get_holdings(p, sym):.4f} {sym}."); return
        price = self.state["prices"][sym]
        fee = self._coin_spec(sym).fee_bps / 10000.0
        proceeds = math.floor(price * qty * (1.0 - fee))
        self._add_holdings(p, sym, -qty)
        self._add_credits(p, +proceeds)
        self._save_holdings_for(p)
        p.send_message(f"§a[Crypto] Sold {qty:.4f} {sym} for {proceeds} credits (after fees).")

    # ── operator/admin commands ──────────────────────────────────────────────
    def _cmd_admin(self, p: Player, rest: List[str]) -> bool:
        if not p.has_permission("endstone_crypto.admin"):
            p.send_message("§c[Crypto] You lack permission endstone_crypto.admin")
            return True

        if not rest or rest[0].lower() in ("help", "?"):
            p.send_message("§b§lCrypto Admin")
            p.send_message("§6/crypto admin on§7 | §6/crypto admin off")
            p.send_message("§6/crypto admin setprice <sym> <price>")
            p.send_message("§6/crypto admin holdings <player|uuid>")
            p.send_message("§6/crypto admin addcredit <player|uuid> <amount>")
            p.send_message("§6/crypto admin takecredit <player|uuid> <amount>")
            p.send_message("§6/crypto admin setcredit <player|uuid> <amount>")
            p.send_message("§6/crypto admin addcoin <player|uuid> <sym> <qty>")
            p.send_message("§6/crypto admin takecoin <player|uuid> <sym> <qty>")
            p.send_message("§6/crypto admin setcoin <player|uuid> <sym> <qty>")
            p.send_message("§6/crypto admin offers [open|all]")
            p.send_message("§6/crypto admin cancel <offer_id>")
            p.send_message("§6/crypto admin purgeoffers")
            return True

        sub = rest[0].lower()

        if sub in ("on", "off"):
            self.cfg.enabled = (sub == "on")
            self._save_config()
            p.send_message("§a[Crypto] Market enabled." if self.cfg.enabled else "§e[Crypto] Market disabled.")
            return True

        if sub == "setprice" and len(rest) >= 3:
            ok, sym, err = self._resolve_symbol(rest[1])
            if not ok:
                p.send_message(err); return True
            try:
                newp = float(rest[2])
            except Exception:
                p.send_message("§c[Crypto] Invalid price."); return True
            spec = self._coin_spec(sym)
            clamped = max(spec.min_price, min(spec.max_price, newp))
            self.state["prices"][sym] = clamped
            self.state["history"][sym].append(clamped)
            self._save_state()
            p.send_message(f"§a[Crypto] Set {sym} price to ${clamped:.2f}.")
            return True

        if sub in ("holdings", "addcredit", "takecredit", "setcredit",
                   "addcoin", "takecoin", "setcoin"):
            if len(rest) < 2:
                p.send_message("§c[Crypto] Missing <player|uuid>."); return True
            tgt_ok, uuid_hex, display, tgt_player = self._resolve_player(rest[1])
            if not tgt_ok:
                p.send_message("§c[Crypto] Player not found (online now or seen before)."); return True

            if sub == "holdings":
                creds = self._get_credits_by_uuid(uuid_hex)
                p.send_message(f"§b§lHoldings for {display}")
                p.send_message(f"§bCredits: §l{creds}")
                inv = self._holdings.get(uuid_hex, {})
                coins = [(s, q) for s, q in inv.items() if s != "_credits" and q > 0]
                if not coins:
                    p.send_message("§7(no coin balances)")
                else:
                    for sym, qty in sorted(coins):
                        price = self.state["prices"].get(sym, 0.0)
                        p.send_message(f"§f{sym} §7x {qty:.4f}  §8(≈ ${qty*price:.2f})")
                return True

            if sub in ("addcredit", "takecredit", "setcredit"):
                if len(rest) < 3:
                    p.send_message("§c[Crypto] Missing amount."); return True
                try:
                    amt = int(float(rest[2]))
                except Exception:
                    p.send_message("§c[Crypto] Invalid amount."); return True
                if sub == "addcredit":
                    self._add_credits_by_uuid(uuid_hex, amt)
                elif sub == "takecredit":
                    self._add_credits_by_uuid(uuid_hex, -abs(amt))
                else:
                    inv = self._holdings.setdefault(uuid_hex, defaultdict(float))
                    inv["_credits"] = int(amt)
                self._save_holdings()
                p.send_message(f"§a[Crypto] Credits updated for {display}.")
                if tgt_player:
                    tgt_player.send_message("§e[Crypto] An operator updated your credits.")
                return True

            if len(rest) < 4:
                p.send_message("§c[Crypto] Missing <sym> <qty>."); return True
            ok, sym, err = self._resolve_symbol(rest[2])
            if not ok:
                p.send_message(err); return True
            try:
                qty = float(rest[3])
            except Exception:
                p.send_message("§c[Crypto] Invalid quantity."); return True
            if sub == "addcoin":
                self._add_holdings_by_uuid(uuid_hex, sym, +qty)
            elif sub == "takecoin":
                self._add_holdings_by_uuid(uuid_hex, sym, -abs(qty))
            else:
                inv = self._holdings.setdefault(uuid_hex, defaultdict(float))
                inv[sym] = max(0.0, qty)
            self._save_holdings()
            p.send_message(f"§a[Crypto] Coin balance updated for {display}.")
            if tgt_player:
                tgt_player.send_message("§e[Crypto] An operator updated your coin balances.")
            return True

        if sub == "offers":
            which = rest[1].lower() if len(rest) >= 2 else "open"
            p.send_message("§b§lOffers (admin)")
            shown = 0
            for oid, o in self._offers.items():
                if which == "open" and o["status"] != "open":
                    continue
                p.send_message(f"§7#{oid} §f{ o['seller_name'] } §8→§f { o['buyer_name'] } §7— {o['qty']:.4f} {o['symbol']} @ {o['price_per']:.4f}/ea §8[{o['status']}]")
                shown += 1
            if shown == 0:
                p.send_message("§7(no offers)")
            return True

        if sub == "cancel" and len(rest) >= 2:
            oid = rest[1]
            if oid in self._offers and self._offers[oid]["status"] == "open":
                self._offers[oid]["status"] = "cancelled"
                self._save_offers()
                p.send_message(f"§e[Crypto] Offer #{oid} cancelled.")
            else:
                p.send_message("§c[Crypto] Offer not found or not open.")
            return True

        if sub == "purgeoffers":
            before = len(self._offers)
            self._offers = {k: v for k, v in self._offers.items() if v.get("status") == "open"}
            self._save_offers()
            p.send_message(f"§a[Crypto] Purged closed offers: {before - len(self._offers)} removed; {len(self._offers)} open remain.")
            return True

        p.send_message("§7Try §6/crypto admin help")
        return True

    # ── price engine / scheduler ─────────────────────────────────────────────
    def _price_tick(self):
        self.state["tick"] += 1
        for spec in self.cfg.coins:
            symbol = spec.symbol
            p0 = self.state["prices"][symbol]
            hist: Deque[float] = self.state["history"][symbol]
            trend = 0.0
            if len(hist) >= 5:
                base = list(hist)[-5]
                trend = (p0 - base) / max(1e-6, base)
            mu = 0.000
            sigma = spec.volatility / (24 * 60 * 60 / max(1, self.cfg.tick_seconds))
            pct = random.gauss(mu, sigma)
            pct = (1.0 - spec.momentum) * pct + spec.momentum * trend * 0.05
            p1 = max(spec.min_price, min(spec.max_price, p0 * (1.0 + pct)))
            self.state["prices"][symbol] = p1
            hist.append(p1)
            while len(hist) > self.cfg.chart_points:
                hist.popleft()

        self._save_state()

    # ── mining helpers ───────────────────────────────────────────────────────
    def _pick_mining_coin(self) -> str:
        weights = [c.mining_weight for c in self.cfg.coins]
        symbols = [c.symbol for c in self.cfg.coins]
        return random.choices(symbols, weights=weights, k=1)[0]

    # ── symbol resolution ────────────────────────────────────────────────────
    def _resolve_symbol(self, raw: str) -> Tuple[bool, Optional[str], str]:
        s = (raw or "").strip().upper()
        if not s:
            return False, None, "§c[Crypto] Missing symbol."
        symbols = self._coin_symbols()
        if s in symbols:
            return True, s, ""
        matches = [sym for sym in symbols if sym.startswith(s)]
        if len(matches) == 1:
            return True, matches[0], ""
        if len(matches) > 1:
            return False, None, f"§e[Crypto] Ambiguous. Matches: {', '.join(matches)}"
        return False, None, "§c[Crypto] Unknown symbol. Use /crypto symbols"

    # ── storage: holdings / credits ──────────────────────────────────────────
    def _get_root(self, p: Player) -> Dict[str, float]:
        return self._holdings.setdefault(p.unique_id.hex, defaultdict(float))

    def _get_holdings(self, p: Player, symbol: str) -> float:
        return float(self._holdings.get(p.unique_id.hex, {}).get(symbol, 0.0))

    def _add_holdings(self, p: Player, symbol: str, delta: float):
        inv = self._get_root(p)
        inv[symbol] = max(0.0, inv.get(symbol, 0.0) + delta)

    def _get_holdings_by_uuid(self, uuid_hex: str, symbol: str) -> float:
        return float(self._holdings.get(uuid_hex, {}).get(symbol, 0.0))

    def _add_holdings_by_uuid(self, uuid_hex: str, symbol: str, delta: float):
        inv = self._holdings.setdefault(uuid_hex, defaultdict(float))
        inv[symbol] = max(0.0, inv.get(symbol, 0.0) + delta)

    # ── Scoreboard Money integration ────────────────────────────────────────
    def _get_money(self, p: Player) -> int:
        """Get player's Money from scoreboard"""
        try:
            scoreboard = self.server.scoreboard
            objective = scoreboard.get_objective("Money")
            if objective is None:
                # Create Money objective if it doesn't exist
                objective = scoreboard.add_objective("Money", Criteria.DUMMY, "§6Money")
            score = objective.get_score(p)
            return score.value if score else 0
        except Exception as e:
            self.logger.warning(f"Failed to get Money for {p.name}: {e}")
            return 0

    def _set_money(self, p: Player, amount: int):
        """Set player's Money on scoreboard"""
        try:
            scoreboard = self.server.scoreboard
            objective = scoreboard.get_objective("Money")
            if objective is None:
                objective = scoreboard.add_objective("Money", Criteria.DUMMY, "§6Money")
            score = objective.get_score(p)
            if score:
                score.value = max(0, int(amount))
        except Exception as e:
            self.logger.warning(f"Failed to set Money for {p.name}: {e}")

    def _add_money(self, p: Player, delta: int):
        """Add/subtract Money from player's scoreboard"""
        current = self._get_money(p)
        self._set_money(p, current + delta)

    # ── Internal credits (legacy) ────────────────────────────────────────────
    def _get_credits(self, p: Player) -> int:
        return int(float(self._holdings.get(p.unique_id.hex, {}).get("_credits", 0)))

    def _get_credits_by_uuid(self, uuid_hex: str) -> int:
        return int(float(self._holdings.get(uuid_hex, {}).get("_credits", 0)))

    def _add_credits(self, p: Player, delta: int):
        inv = self._get_root(p)
        inv["_credits"] = int(float(inv.get("_credits", 0))) + int(delta)

    def _add_credits_by_uuid(self, uuid_hex: str, delta: int):
        inv = self._holdings.setdefault(uuid_hex, defaultdict(float))
        inv["_credits"] = int(float(inv.get("_credits", 0))) + int(delta)

    def _save_holdings_for(self, p: Player):
        self._save_holdings()

    # ── player index (for offline admin control) ─────────────────────────────
    def _resolve_player(self, name_or_uuid: str) -> Tuple[bool, Optional[str], str, Optional[Player]]:
        # online?
        online = self.server.get_player(name_or_uuid)
        if online is not None:
            return True, online.unique_id.hex, online.name, online

        s = name_or_uuid.strip()
        if re.fullmatch(r"[0-9a-fA-F]{32}", s):
            display = self._players_index.get(s.lower(), s.lower())
            return True, s.lower(), display, None

        name_lower = s.lower()
        for uuid_hex, display in self._players_index.items():
            if display.lower() == name_lower:
                return True, uuid_hex, display, None
        return False, None, "", None

    # ── charts ───────────────────────────────────────────────────────────────
    _sparks = "▁▂▃▄▅▆▇█"

    def _mini_chart(self, symbol: str, tall: bool=False) -> str:
        data = list(self.state["history"][symbol])
        if not data:
            return "No data."
        mn, mx = min(data), max(data)
        rng = (mx - mn) or 1e-6
        bars = []
        for v in data[-self.cfg.chart_points:]:
            idx = int((v - mn) / rng * (len(self._sparks)-1))
            bars.append(self._sparks[idx])
        line = "".join(bars)
        header = f"§7[{symbol}] {self.cfg.chart_points}t history"
        if tall:
            return f"§8{header}\n{line}\n{line}\n{line}"
        return f"§8{header}\n{line}"

    # ── files ────────────────────────────────────────────────────────────────
    def _init_files(self):
        self.data_dir: Path = self.data_folder
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.data_dir / "config.toml"
        self.state_path = self.data_dir / "state.json"
        self.holdings_path = self.data_dir / "holdings.json"
        self.offers_path = self.data_dir / "offers.json"
        self.players_idx_path = self.data_dir / "players.json"

        if not self.config_path.exists():
            default = self._default_config_toml()
            self.config_path.write_text(default, encoding="utf-8")

    def _load_config(self):
        import tomllib  # Python 3.11+
        raw = tomllib.loads(self.config_path.read_text(encoding="utf-8"))
        coins = [CoinSpec(**c) for c in raw["coins"]]
        self.cfg = Config(
            enabled=raw.get("enabled", True),
            tick_seconds=raw.get("tick_seconds", 30),
            chart_points=raw.get("chart_points", 60),
            broadcast_every=raw.get("broadcast_every", 4),
            award_min_depth=raw.get("award_min_depth", 16),
            base_drop_chance=raw.get("base_drop_chance", 0.005),
            ores=raw.get("ores", {}),
            coins=coins,
        )

    def _save_config(self):
        pass

    def _load_state(self):
        loaded_state = False
        if self.state_path.exists():
            try:
                raw = self.state_path.read_text(encoding="utf-8").strip()
                if raw:
                    self.state = json.loads(raw)
                    for k, arr in list(self.state.get("history", {}).items()):
                        dq: Deque[float] = deque(arr, maxlen=self.cfg.chart_points)
                        self.state["history"][k] = dq
                    loaded_state = True
                else:
                    self.logger.warning("state.json is empty, reinitializing...")
            except json.JSONDecodeError as e:
                self.logger.warning(f"state.json corrupted ({e}), reinitializing...")

        if not loaded_state:
            prices = {c.symbol: c.start_price for c in self.cfg.coins}
            history = {c.symbol: deque([c.start_price], maxlen=self.cfg.chart_points) for c in self.cfg.coins}
            self.state = {"tick": 0, "prices": prices, "history": history}
            self._save_state()

        if self.holdings_path.exists():
            try:
                raw = self.holdings_path.read_text(encoding="utf-8").strip()
                if raw:
                    self._holdings = json.loads(raw)
                else:
                    self.logger.warning("holdings.json is empty, reinitializing...")
                    self._holdings: Dict[str, Dict[str, float]] = {}
                    self._save_holdings()
            except json.JSONDecodeError as e:
                self.logger.warning(f"holdings.json corrupted ({e}), reinitializing...")
                self._holdings: Dict[str, Dict[str, float]] = {}
                self._save_holdings()
        else:
            self._holdings: Dict[str, Dict[str, float]] = {}
            self._save_holdings()

    def _save_state(self):
        serial = {"tick": self.state["tick"], "prices": self.state["prices"],
                  "history": {k: list(v) for k, v in self.state["history"].items()}}
        self.state_path.write_text(json.dumps(serial), encoding="utf-8")

    def _save_holdings(self):
        self.holdings_path.write_text(json.dumps(self._holdings), encoding="utf-8")

    def _load_offers(self):
        loaded = False
        if self.offers_path.exists():
            try:
                raw_text = self.offers_path.read_text(encoding="utf-8").strip()
                if raw_text:
                    raw = json.loads(raw_text)
                    self._offers = raw.get("offers", {})
                    self._next_offer_id = int(raw.get("next_id", 1))
                    loaded = True
                else:
                    self.logger.warning("offers.json is empty, reinitializing...")
            except json.JSONDecodeError as e:
                self.logger.warning(f"offers.json corrupted ({e}), reinitializing...")
        if not loaded:
            self._offers: Dict[str, Dict] = {}
            self._next_offer_id = 1
            self._save_offers()

    def _save_offers(self):
        self.offers_path.write_text(json.dumps({"next_id": self._next_offer_id, "offers": self._offers}), encoding="utf-8")

    def _load_players_index(self):
        loaded = False
        if self.players_idx_path.exists():
            try:
                raw = self.players_idx_path.read_text(encoding="utf-8").strip()
                if raw:
                    self._players_index = json.loads(raw)
                    loaded = True
                else:
                    self.logger.warning("players.json is empty, reinitializing...")
            except json.JSONDecodeError as e:
                self.logger.warning(f"players.json corrupted ({e}), reinitializing...")
        if not loaded:
            self._players_index: Dict[str, str] = {}
            self._save_players_index()

    def _save_players_index(self):
        self.players_idx_path.write_text(json.dumps(self._players_index), encoding="utf-8")

    # ── utils ────────────────────────────────────────────────────────────────
    def _find_player_by_uuid_hex(self, uuid_hex: str) -> Optional[Player]:
        for pl in list(self.server.online_players):
            if getattr(pl.unique_id, "hex", "") == uuid_hex:
                return pl
        return None

    def _coin_symbols(self) -> List[str]:
        return [c.symbol for c in self.cfg.coins]

    def _coin_spec(self, symbol: str) -> CoinSpec:
        for c in self.cfg.coins:
            if c.symbol == symbol:
                return c
        raise KeyError(symbol)

    def _default_config_toml(self) -> str:
        return """\
enabled = true
tick_seconds = 30
chart_points = 60
broadcast_every = 4
award_min_depth = 16
base_drop_chance = 0.004

[ores]
"minecraft:coal_ore" = 0.6
"minecraft:iron_ore" = 0.8
"minecraft:copper_ore" = 0.5
"minecraft:gold_ore" = 1.0
"minecraft:redstone_ore" = 1.2
"minecraft:lapis_ore" = 1.1
"minecraft:diamond_ore" = 2.0
"minecraft:emerald_ore" = 2.4
"minecraft:deepslate_diamond_ore" = 2.8
"minecraft:ancient_debris" = 3.2

[[coins]]
symbol = "NINJ"
name = "Ninjos Enterprise"
start_price = 50.0
min_price = 1.0
max_price = 5000.0
volatility = 0.25
mining_weight = 1.2
momentum = 0.10
fee_bps = 30

[[coins]]
symbol = "DIAM"
name = "Diamond Coperation"
start_price = 250.0
min_price = 5.0
max_price = 10000.0
volatility = 0.35
mining_weight = 0.8
momentum = 0.08
fee_bps = 25

[[coins]]
symbol = "EMER"
name = "Emerald Vale"
start_price = 140.0
min_price = 3.0
max_price = 7000.0
volatility = 0.30
mining_weight = 0.9
momentum = 0.08
fee_bps = 25

[[coins]]
symbol = "RED"
name = "Redstone Industries"
start_price = 25.0
min_price = 0.5
max_price = 500.0
volatility = 0.20
mining_weight = 1.4
momentum = 0.06
fee_bps = 15

[[coins]]
symbol = "OBSID"
name = "Obsidian Core"
start_price = 80.0
min_price = 1.0
max_price = 4000.0
volatility = 0.28
mining_weight = 0.6
momentum = 0.09
fee_bps = 20

[[coins]]
symbol = "NTHR"
name = "Netherium Core Inc."
start_price = 1200.0
min_price = 100.0
max_price = 25000.0
volatility = 0.45
mining_weight = 0.2
momentum = 0.12
fee_bps = 40

[[coins]]
symbol = "AURUM"
name = "Aurum Reserve"
start_price = 110.0
min_price = 2.0
max_price = 6000.0
volatility = 0.32
mining_weight = 1.0
momentum = 0.07
fee_bps = 22

[[coins]]
symbol = "FERRO"
name = "Ferrous Consolidated"
start_price = 35.0
min_price = 0.8
max_price = 750.0
volatility = 0.18
mining_weight = 1.5
momentum = 0.05
fee_bps = 18

[[coins]]
symbol = "LAZUL"
name = "Lazuli Analytics"
start_price = 65.0
min_price = 1.5
max_price = 3000.0
volatility = 0.26
mining_weight = 1.1
momentum = 0.09
fee_bps = 20

[[coins]]
symbol = "QRTZ"
name = "Quartz Holdings"
start_price = 45.0
min_price = 1.0
max_price = 1500.0
volatility = 0.22
mining_weight = 1.3
momentum = 0.07
fee_bps = 17

[[coins]]
symbol = "EPORT"
name = "EnderPort Logistics"
start_price = 200.0
min_price = 10.0
max_price = 8000.0
volatility = 0.38
mining_weight = 0.5
momentum = 0.11
fee_bps = 35

[[coins]]
symbol = "NSTAR"
name = "NetherStar Capital"
start_price = 5000.0
min_price = 500.0
max_price = 100000.0
volatility = 0.60
mining_weight = 0.1
momentum = 0.15
fee_bps = 50

[[coins]]
symbol = "IGNIS"
name = "Ignis Industries"
start_price = 180.0
min_price = 8.0
max_price = 4500.0
volatility = 0.33
mining_weight = 0.7
momentum = 0.10
fee_bps = 28

[[coins]]
symbol = "SHULK"
name = "Shulker Storage Solutions"
start_price = 750.0
min_price = 50.0
max_price = 15000.0
volatility = 0.40
mining_weight = 0.3
momentum = 0.13
fee_bps = 38

[[coins]]
symbol = "AVIA"
name = "Avia Dynamics"
start_price = 3500.0
min_price = 300.0
max_price = 50000.0
volatility = 0.50
mining_weight = 0.15
momentum = 0.14
fee_bps = 45

[[coins]]
symbol = "UNDY"
name = "Undying Ventures"
start_price = 1500.0
min_price = 150.0
max_price = 30000.0
volatility = 0.48
mining_weight = 0.25
momentum = 0.12
fee_bps = 42

[[coins]]
symbol = "MARIN"
name = "Prismarine Maritime"
start_price = 90.0
min_price = 4.0
max_price = 3500.0
volatility = 0.29
mining_weight = 0.8
momentum = 0.08
fee_bps = 24

[[coins]]
symbol = "SENS"
name = "Sculk Sensors Ltd."
start_price = 400.0
min_price = 20.0
max_price = 9000.0
volatility = 0.36
mining_weight = 0.4
momentum = 0.11
fee_bps = 33

[[coins]]
symbol = "AMETH"
name = "Amethyst Geode Group"
start_price = 120.0
min_price = 5.0
max_price = 5000.0
volatility = 0.31
mining_weight = 0.9
momentum = 0.09
fee_bps = 26

[[coins]]
symbol = "LUX"
name = "Lux Industries"
start_price = 20.0
min_price = 0.4
max_price = 400.0
volatility = 0.19
mining_weight = 1.6
momentum = 0.06
fee_bps = 14

[[coins]]
symbol = "ANDEB"
name = "Ancient Debris Mining"
start_price = 800.0
min_price = 75.0
max_price = 18000.0
volatility = 0.42
mining_weight = 0.3
momentum = 0.13
fee_bps = 37

[[coins]]
symbol = "OCEAN"
name = "Oceanic Trust"
start_price = 600.0
min_price = 40.0
max_price = 12000.0
volatility = 0.39
mining_weight = 0.35
momentum = 0.10
fee_bps = 32

[[coins]]
symbol = "ABSOR"
name = "Absorbent Systems"
start_price = 220.0
min_price = 15.0
max_price = 6000.0
volatility = 0.34
mining_weight = 0.6
momentum = 0.09
fee_bps = 29

[[coins]]
symbol = "SLMTK"
name = "SlimeTek Innovations"
start_price = 55.0
min_price = 2.0
max_price = 2000.0
volatility = 0.27
mining_weight = 1.0
momentum = 0.07
fee_bps = 21

[[coins]]
symbol = "BCON"
name = "Beacon Financial"
start_price = 8000.0
min_price = 1000.0
max_price = 150000.0
volatility = 0.65
mining_weight = 0.05
momentum = 0.18
fee_bps = 60

[[coins]]
symbol = "DRAC"
name = "Draconic Elixirs"
start_price = 300.0
min_price = 25.0
max_price = 7500.0
volatility = 0.37
mining_weight = 0.45
momentum = 0.12
fee_bps = 34

[[coins]]
symbol = "OVOID"
name = "The Ovoid Foundation"
start_price = 20000.0
min_price = 2500.0
max_price = 500000.0
volatility = 0.80
mining_weight = 0.01
momentum = 0.20
fee_bps = 100

[[coins]]
symbol = "EXPLO"
name = "Explosives Co."
start_price = 70.0
min_price = 3.0
max_price = 2500.0
volatility = 0.28
mining_weight = 1.1
momentum = 0.08
fee_bps = 23

[[coins]]
symbol = "GTEAR"
name = "Ghast Tear Solutions"
start_price = 250.0
min_price = 18.0
max_price = 6500.0
volatility = 0.35
mining_weight = 0.55
momentum = 0.11
fee_bps = 31

[[coins]]
symbol = "MAGCO"
name = "MagmaCorp"
start_price = 100.0
min_price = 5.0
max_price = 4000.0
volatility = 0.30
mining_weight = 0.95
momentum = 0.09
fee_bps = 25

[[coins]]
symbol = "WTHSC"
name = "Witherforce Securities"
start_price = 1800.0
min_price = 200.0
max_price = 40000.0
volatility = 0.55
mining_weight = 0.2
momentum = 0.16
fee_bps = 48

[[coins]]
symbol = "TRIDT"
name = "Trident Maritime"
start_price = 1300.0
min_price = 120.0
max_price = 28000.0
volatility = 0.46
mining_weight = 0.28
momentum = 0.14
fee_bps = 41

[[coins]]
symbol = "CARBN"
name = "Carbon Fuel Group"
start_price = 10.0
min_price = 0.2
max_price = 200.0
volatility = 0.15
mining_weight = 1.8
momentum = 0.04
fee_bps = 10

[[coins]]
symbol = "APIS"
name = "Apis Holdings"
start_price = 40.0
min_price = 1.0
max_price = 1200.0
volatility = 0.24
mining_weight = 1.2
momentum = 0.07
fee_bps = 16
"""
