StartupEvents.registry('item', event => {
 event.create('casino_coin').displayName('Casino Coin').texture('easy_npc:item/consumable/npc_coin');
 event.create('resonant_core').displayName(Text.translate('item.kubejs.resonant_core')).texture('ars_nouveau:item/source_gem');
 event.create('attuned_core').displayName(Text.translate('item.kubejs.attuned_core')).texture('ae2:item/fluix_crystal');
 event.create('divine_core').displayName(Text.translate('item.kubejs.divine_core')).texture('divinerpg:item/eden_gem');
 event.create('heart_of_eldoria').displayName(Text.translate('item.kubejs.heart_of_eldoria')).texture('minecraft:item/nether_star').glow(true);
});
