/* 
Thank you to asportnoy#6969 for providing the majority of this code 
I've just edited this to make it update our db
*/

const { MongoClient } = require('mongodb');
const fetch = require('node-fetch');
const uri = `mongodb+srv://${process.env.Mongo_User}:${process.env.Mongo_Pass}@carltagscluster.nyxt2.mongodb.net/TagDB?retryWrites=true&w=majority`;

const client = new MongoClient(uri);


(async () => {
	await client.connect();

	const db = client.db('TagDB');
	const tags = db.collection('Tags');
	let latestID = await tags.find().sort({ _id: -1}).limit(1);
	let rangeCount = 0;

	async function requestTag(id) {
		try {
			const res = await fetch(`https://carl.gg/api/v1/tags/${id}`);
			if (res.status == 200) {
				const text = await res.json();
				const json = JSON.parse(text);
				const data = {
					_id: json.id,
					created_at: new Date(json.created_at),
					guild_id: /"location_id":\s*(\d+)/.exec(text)[1],
					tag_name: json.name,
					nsfw: json.nsfw,
					owner_id: json.owner_id,
					sharer: json.sharer,
					uses: json.uses,
					content: json.content,
					embed: json.embed,
					last_fetched: new Date(),
					deleted: false,
				};

				rangeCount = 1;
				latestID = await tags.find().sort({ _id: -1}).limit(1);

				tags.updateOne(
					{_id: json.id},
					{$set: data},
					{upsert: true},
				).then(() => console.log(`Saved Tag ID: ${id}`));
			} else if (res.status == 404) {
				const dbDoc = await tags.findOne({_id: id});
				if (dbDoc) {
					tags.updateOne(
						{_id: id},
						{$set: {deleted: true, last_fetched: new Date()}},
					).then(() => console.log(`Deleted Tag ID: ${id}`));
				}
			} else {
				console.log(`Tag ${id} Failed: Error ${res.status}, sleeping for 3 seconds`);
				await new Promise(resolve => setTimeout(resolve, 3000));
				return await requestTag(id);
			}
		} catch (error) {
			console.log(`Tag ${id} Failed`);
			console.error(error);
		}
	}

	async function process() {
		await requestTag(latestID + rangeCount);
		rangeCount++;

		if (rangeCount % 500 == 0) {
			rangeCount = 0
			console.log(`Checked range to ${newID - 500} - ${newID}, no tags found, resetting...`);
		}
		setTimeout(process, 500);
	}

	
	for (let i = 0; i > 0; i++) {
		process();
	}
})();
