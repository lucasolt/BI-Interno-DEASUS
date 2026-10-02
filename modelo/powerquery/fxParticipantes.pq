// Coordenador + texto da EQUIPE -> lista de [Função, Nome].
// Equipe separada por ; , / ou " e ". Sem ninguém: um coordenador nulo (vira "(Não informado)").
(coordenador as nullable text, equipe as nullable text) as list =>
let
    Coord = if coordenador = null then {} else {[Função = "Coordenador", Nome = coordenador]},
    EqNorm = if equipe = null then null
             else List.Accumulate({" e ", " E ", ",", "/"}, equipe, (s, sep) => Text.Replace(s, sep, ";")),
    EqLista = if EqNorm = null then {}
              else List.Select(List.Transform(Text.Split(EqNorm, ";"), Text.Trim), each _ <> "" and _ <> "-"),
    Equipe = List.Transform(EqLista, each [Função = "Equipe", Nome = _]),
    Todos = Coord & Equipe
in
    if List.IsEmpty(Todos) then {[Função = "Coordenador", Nome = null]} else Todos
