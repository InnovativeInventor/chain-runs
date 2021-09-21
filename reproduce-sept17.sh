python chains.py VA 50000 sep17 11 
python chains.py VA 50000 sep17 40 
python chains.py VA 50000 sep17 100 

python chains.py VA 50000 sep17 11 --optimize agg_prop
python chains.py VA 50000 sep17 40 --optimize agg_prop
python chains.py VA 50000 sep17 100 --optimize agg_prop

python chains.py VA 50000 sep17 11 --optimize agg_prop_abs
python chains.py VA 50000 sep17 40 --optimize agg_prop_abs
python chains.py VA 50000 sep17 100 --optimize agg_prop_abs

python chains.py MI 50000 sep17 13 --pop-col TOTPOP
python chains.py MI 50000 sep17 38 --pop-col TOTPOP
python chains.py MI 50000 sep17 110 --pop-col TOTPOP

python chains.py MI 50000 sep17 13 --optimize agg_prop --pop-col TOTPOP
python chains.py MI 50000 sep17 38 --optimize agg_prop --pop-col TOTPOP
python chains.py MI 50000 sep17 110 --optimize agg_prop --pop-col TOTPOP

python chains.py MI 50000 sep17 13 --optimize agg_prop_abs --pop-col TOTPOP
python chains.py MI 50000 sep17 38 --optimize agg_prop_abs --pop-col TOTPOP
python chains.py MI 50000 sep17 110 --optimize agg_prop_abs --pop-col TOTPOP
