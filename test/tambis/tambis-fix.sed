grep _anon tambis-full.daml | sed -e 's/.*\(_anon[0-9]*\).*/     <\1>,/g' > anons
