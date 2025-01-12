from pandas import DataFrame

from object_centric.object_type_structure import ObjectTypeStructure, ObjectType, Multiplicity


def read_initial_marking(ocel_path, ot_struct: ObjectTypeStructure, fraction=None) -> dict[ObjectType, DataFrame]:
    """
    Because object generation is a topic for itself: Make possible a simulation using the
    initial marking (object graph) from some existing event log.

    :param ocel_path: Where the OCEL can be found.
    :param ot_struct: The marking is to be projected according to type structure, i.e., the subset of object types and relations indicated in ot_struct.
    :param fraction:

    :return: For each object type, a DataFrame, containing object ID, arrival time, and for related object types, either a list of IDs or a single ID, depending on the relationship multiplicity.
    """
    initial_marking: dict[ObjectType, DataFrame] = dict()
    import sqlite3
    import pandas as pd
    conn = sqlite3.connect(ocel_path)
    for ot in ot_struct.get_object_types():
        ot_table_name = "object_" + ot.get_name()[0].upper() + ot.get_name()[1:]
        ot_df = pd.read_sql_query(f"SELECT * FROM {ot_table_name}", conn)
        ot_df_initial = ot_df[ot_df["ocel_changed_field"].isna()]
        ot_df_initial_relative_times = ot_df_initial[["ocel_id", "ocel_time"]][:]
        ot_df_initial_relative_times["ocel_time"] = pd.to_datetime(
            ot_df_initial_relative_times["ocel_time"]
        )
        ot_df_initial_relative_times["ocel_time"] = ot_df_initial_relative_times["ocel_time"].apply(
            lambda x: x.timestamp()
        )
        #max_time = ot_df_initial_relative_times["ocel_time"].max()
        min_time = ot_df_initial_relative_times["ocel_time"].min()
        ot_df_initial_relative_times["ocel_time"] = ot_df_initial_relative_times["ocel_time"].apply(
            lambda t: t - min_time
        )
        initial_marking[ot] = ot_df_initial_relative_times
    o2o = pd.read_sql_query("SELECT * FROM object_object", conn)
    o = pd.read_sql_query("SELECT * FROM object", conn)
    o2o_t = o2o.\
        merge(o[["ocel_id", "ocel_type"]].rename(columns={"ocel_id": "ocel_source_id", "ocel_type": "ocel_source_type"}), on="ocel_source_id").\
        merge(o[["ocel_id", "ocel_type"]].rename(columns={"ocel_id": "ocel_target_id", "ocel_type": "ocel_target_type"}), on="ocel_target_id")
    for r in ot_struct.get_object_type_relations():
        ot1 = r.get_ot1()
        ot2 = r.get_ot2()
        m1 = r.get_m1()
        m2 = r.get_m2()
        o2o_r = o2o_t[(o2o_t["ocel_source_type"] == ot1.get_name()) & (o2o_t["ocel_target_type"] == ot2.get_name())][["ocel_source_id", "ocel_target_id"]]
        ot1_df = initial_marking[ot1]
        ot2_df = initial_marking[ot2]
        ot1_df_ot2 = ot1_df.merge(o2o_r.rename(columns={"ocel_source_id": "ocel_id"})).rename(columns=({"ocel_target_id": ot2.get_name()}))
        ot2_df_ot1 = ot2_df.merge(o2o_r.rename(columns={"ocel_target_id": "ocel_id"})).rename(columns=({"ocel_source_id": ot1.get_name()}))
        for (ot_a, ot_a_df, ot_a_df_ot_b, m, ot_b) in [(ot1, ot1_df, ot1_df_ot2, m2, ot2), (ot2, ot2_df, ot2_df_ot1, m1, ot1)]:
            if m is Multiplicity.MANY:
                ot_a_cols = ot_a_df.columns
                grouping_columns = ["ocel_id", "ocel_time", ot_b.get_name()]
                ot_a_df_ot_b = ot_a_df_ot_b[grouping_columns]
                ot_a_df_1 = ot_a_df_ot_b.groupby('ocel_id').agg({'ocel_time': 'first', ot_b.get_name(): lambda z: list(z)}).reset_index()
                ot_a_df_2 = ot_a_df[["ocel_id"] + [col for col in ot_a_cols if col not in grouping_columns]]
                ot_a_df = pd.merge(ot_a_df_1, ot_a_df_2, on="ocel_id")
                if ot_a == ot1:
                    ot1_df = ot_a_df
                if ot_a == ot2:
                    ot2_df = ot_a_df
            else:
                ot2_df = ot2_df_ot1
        initial_marking[ot1] = ot1_df
        initial_marking[ot2] = ot2_df
    conn.close()
    return initial_marking