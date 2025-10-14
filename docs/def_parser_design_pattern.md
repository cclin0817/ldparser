
I divide the sections in def into 

1. variable section (Single line with structure {key value })
2. With dash blcok section (multi-line {key ...; })
3. Without dash block section (multi-sections { [- key value, + properties]})

Hierachy structure of W/O dash Block:
{Block: {
    section (start with "-", end with ";"):{
        head (start with -, single line): single_line,
        properties (a block with hierachy +): list of sinlge_line
    }
}
}

To handle this situation, I use "single-responsibility principal" to create different responsibility class:

1. BaseParser
    1. HeaderParser
    2. BlockParserNoEnd
    3. BlockParserWithEnd
        1. DashParser
2. Transformer class:
    1. BlockTransformer
        2. SectionTransformer
            4. LineFormatter
            5. LineSeperator
            6. LineClearer

By following the OCP (open-extension, closed modification principal), if one want to :

1. Add a Block transformer, he can inheritate "BlockTransformer", then create a new class
2. If only want to transform a block with no property content info needed, he can follow following example to create new block parser:

```

component_block_transformer = NoPropertyBlockTransformer(
    CommonLineClearer(),
    CommonLineSeperator(),
    ComponentHeadFormatter()
)

net_block_transformer = NoPropertyBlockTransformer(
    CommonLineClearer(),
    CommonLineSeperator(),
    NetHeadFormatter()
)
```
