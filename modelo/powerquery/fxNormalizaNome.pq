// Chave de comparação de nomes: minúsculas, sem acentos, espaços/quebras de linha colapsados.
// Ex.: "Katlei#(lf)MAGÁLI  Kussler" -> "katlei magali kussler"
(nome as nullable text) as nullable text =>
let
    Minusculo = if nome = null then null else Text.Lower(nome),
    Pares = {
        {"á","a"},{"à","a"},{"â","a"},{"ã","a"},{"ä","a"},
        {"é","e"},{"è","e"},{"ê","e"},{"ë","e"},
        {"í","i"},{"ì","i"},{"î","i"},{"ï","i"},
        {"ó","o"},{"ò","o"},{"ô","o"},{"õ","o"},{"ö","o"},
        {"ú","u"},{"ù","u"},{"û","u"},{"ü","u"},
        {"ç","c"},{"ñ","n"}
    },
    SemAcento = if Minusculo = null then null else List.Accumulate(Pares, Minusculo, (s, p) => Text.Replace(s, p{0}, p{1})),
    Partes = if SemAcento = null then {} else List.Select(Text.SplitAny(SemAcento, " #(lf)#(cr)#(tab)#(00A0)"), each _ <> ""),
    Resultado = if List.IsEmpty(Partes) then null else Text.Combine(Partes, " ")
in
    Resultado
