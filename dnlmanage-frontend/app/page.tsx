"use client";

import { useState } from "react";

export default function Home() {
  const [formData, setFormData] = useState({
    claim_number: "",
    customer_name: "",
    policy_number: "",
    amount: "",
  });

  const [response, setResponse] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (
    e: React.FormEvent
  ) => {
    e.preventDefault();

    setLoading(true);

    try {
      const res = await fetch(
        "http://localhost:8000/ingestion/form",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",

            // Add auth token if needed
            Authorization: `Bearer YOUR_TOKEN_HERE`,
          },

          body: JSON.stringify({
            data: {
              ...formData,
              amount: parseFloat(formData.amount),
            },
          }),
        }
      );

      const result = await res.json();

      setResponse(result);

    } catch (err) {
      console.error(err);
    }

    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-gray-100 p-10">
      <div className="max-w-2xl mx-auto bg-white p-8 rounded-xl shadow">

        <h1 className="text-3xl font-bold mb-6">
          Claim Intake Form
        </h1>

        <form
          onSubmit={handleSubmit}
          className="space-y-4"
        >

          <input
            type="text"
            name="claim_number"
            placeholder="Claim Number"
            className="w-full border p-3 rounded"
            onChange={handleChange}
          />

          <input
            type="text"
            name="customer_name"
            placeholder="Customer Name"
            className="w-full border p-3 rounded"
            onChange={handleChange}
          />

          <input
            type="text"
            name="policy_number"
            placeholder="Policy Number"
            className="w-full border p-3 rounded"
            onChange={handleChange}
          />

          <input
            type="number"
            name="amount"
            placeholder="Amount"
            className="w-full border p-3 rounded"
            onChange={handleChange}
          />

          <button
            type="submit"
            className="bg-black text-white px-6 py-3 rounded"
          >
            {loading ? "Submitting..." : "Submit"}
          </button>
        </form>

        {response && (
          <div className="mt-6 p-4 bg-gray-50 rounded">
            <h2 className="font-bold mb-2">
              API Response
            </h2>

            <pre className="text-sm overflow-auto">
              {JSON.stringify(response, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </main>
  );
}